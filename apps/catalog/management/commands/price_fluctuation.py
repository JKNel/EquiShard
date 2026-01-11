"""
Price Fluctuation Background Service

A Django management command that runs as a background service to simulate
real-time price movements for assets. Configurable via environment variables.
"""

import os
import random
import time
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = 'Run price fluctuation service for simulating market movements'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=int(os.getenv('PRICE_FLUCTUATION_INTERVAL', '60')),
            help='Interval in seconds between price updates (default: 60)'
        )

        # Get defaults from env or use safe defaults (5%)
        # These are expected to be integers or floats representing percentages (e.g. 5 for 5%)
        env_max = float(os.getenv('MAX_INCREASE_PERCENTAGE', '5'))
        env_min = float(os.getenv('MAX_DECREASE_PERCENTAGE', '5'))

        # Convert to decimal for calculation (5 -> 0.05)
        default_max = env_max / 100.0
        # For decrease, we want the negative value (5 -> -0.05)
        default_min = -(env_min / 100.0)

        parser.add_argument(
            '--min-change',
            type=float,
            default=default_min,
            help=f'Minimum price change percentage (default: {default_min:.4f} from negative {env_min}%)'
        )
        parser.add_argument(
            '--max-change',
            type=float,
            default=default_max,
            help=f'Maximum price change percentage (default: {default_max:.4f} from {env_max}%)'
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Run only once instead of continuously'
        )

    def handle(self, *args, **options):
        interval = options['interval']
        min_change = options['min_change']
        max_change = options['max_change']
        run_once = options['once']

        self.stdout.write(self.style.SUCCESS(
            f'Starting Price Fluctuation Service\n'
            f'  Interval: {interval}s\n'
            f'  Range: {min_change*100:.0f}% to {max_change*100:.0f}%'
        ))

        while True:
            try:
                self.update_prices(min_change, max_change)
                
                if run_once:
                    break
                    
                self.stdout.write(f'Next update in {interval} seconds...')
                time.sleep(interval)
                
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('\nPrice fluctuation service stopped.'))
                break
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error: {e}'))
                if run_once:
                    break
                time.sleep(10)  # Wait before retry

    @transaction.atomic
    def update_prices(self, min_change: float, max_change: float):
        """Update all asset prices with random fluctuation."""
        from apps.catalog.models import Asset, AssetPriceHistory
        from datetime import datetime
        
        assets = Asset.objects.filter(is_active=True)
        updated_count = 0
        history_records = []
        
        for asset in assets:
            # Random percentage change between min and max
            change_percent = random.uniform(min_change, max_change)
            
            # Calculate new price (minimum $0.01)
            old_price = float(asset.valuation)
            new_price = max(0.01, old_price * (1 + change_percent))
            
            # Update asset valuation
            asset.valuation = Decimal(str(round(new_price, 8)))
            asset.save(update_fields=['valuation', 'updated_at'])
            
            # Create price history record
            history_records.append(AssetPriceHistory(
                asset=asset,
                price=asset.valuation,
                volume=Decimal(str(round(random.uniform(100, 10000), 2))),
                recorded_at=datetime.now()
            ))
            
            updated_count += 1
            
            # Log significant changes
            if abs(change_percent) > 0.1:
                direction = '📈' if change_percent > 0 else '📉'
                self.stdout.write(
                    f'  {direction} {asset.symbol}: ${old_price:.2f} → ${new_price:.2f} ({change_percent*100:+.1f}%)'
                )
        
        # Bulk create history records
        AssetPriceHistory.objects.bulk_create(history_records)
        
        self.stdout.write(self.style.SUCCESS(
            f'Updated {updated_count} asset prices at {datetime.now().strftime("%H:%M:%S")}'
        ))
