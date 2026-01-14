from decimal import Decimal
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from apps.users.models import User, UserPosition

def get_leaderboard_data(current_user=None, limit=10):
    """
    Calculate profit/loss for all users and return the leaderboard.
    
    Returns:
        dict: {
            'top_users': list of dicts with rank, user, profit_loss,
            'user_rank': dict with rank, profit_loss (if current_user provided)
        }
    """
    # Get all users who have positions
    users_with_positions = User.objects.filter(positions__isnull=False).distinct()
    
    leaderboard = []
    
    for user in users_with_positions:
        # Calculate total P/L across all positions
        total_pl = Decimal('0.00')
        positions = user.positions.select_related('asset').all()
        
        for pos in positions:
            # Current Value = Shares * Current Price
            current_value = pos.shares * pos.asset.valuation
            # Cost Basis = Shares * Avg Cost
            cost_basis = pos.shares * pos.average_cost
            
            # P/L = Current Value - Cost Basis
            total_pl += (current_value - cost_basis)
            
        leaderboard.append({
            'user': user,
            'username': user.username,
            'profit_loss': total_pl
        })
    
    # Sort by Profit/Loss descending
    leaderboard.sort(key=lambda x: x['profit_loss'], reverse=True)
    
    # Add rank
    for i, entry in enumerate(leaderboard):
        entry['rank'] = i + 1
        
    result = {
        'top_users': leaderboard[:limit]
    }
    
    # Find current user's rank if provided
    if current_user and current_user.is_authenticated:
        user_entry = next((item for item in leaderboard if item['user'].id == current_user.id), None)
        if user_entry:
            result['user_rank'] = user_entry
            
    return result
