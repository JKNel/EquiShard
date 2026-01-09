# EquiShard User Details & Roles

## Overview

The platform supports multi-tenancy with three user tiers based on **ABAC (Attribute-Based Access Control)** attributes.

---

## User Roles

### 1. Regular Investor
| Attribute | Value |
|-----------|-------|
| `risk_tolerance` | 1-3 |
| `is_accredited` | `false` |

**Capabilities:**
- Browse and invest in standard assets
- View portfolio analytics
- Use faucet to add test funds
- Access assets with risk level ≤ their tolerance

**Restrictions:**
- Cannot invest in accredited-only assets
- Cannot invest in high-risk (4-5) assets

---

### 2. Growth Investor
| Attribute | Value |
|-----------|-------|
| `risk_tolerance` | 4 |
| `is_accredited` | `false` |

**Capabilities:**
- All Regular Investor capabilities
- Access to higher-risk assets (risk level 4)

**Restrictions:**
- Cannot invest in accredited-only assets
- Cannot invest in maximum risk (5) assets

---

### 3. VIP / Accredited Investor
| Attribute | Value |
|-----------|-------|
| `risk_tolerance` | 5 |
| `is_accredited` | `true` |

**Capabilities:**
- Full platform access
- All asset types including private equity, venture funds
- Maximum risk tolerance

**Restrictions:**
- None (full access)

---

## Test Users (Per Tenant)

### System Administrator (Global)
| Username | Password | Role |
|----------|----------|------|
| `admin` | `password123` | Superuser / Django Admin |

After running `python scripts/seed.py`:

### Alpha Investments Tenant

| Username | Password | Role | Balance |
|----------|----------|------|---------|
| `investor1_alpha` | `password123` | Regular (risk 3) | $10,000 |
| `investor2_alpha` | `password123` | Growth (risk 4) | $25,000 |
| `vip_investor_alpha` | `password123` | VIP Accredited (risk 5) | $100,000 |

### Beta Capital Tenant

| Username | Password | Role | Balance |
|----------|----------|------|---------|
| `investor1_beta` | `password123` | Regular (risk 3) | $10,000 |
| `investor2_beta` | `password123` | Growth (risk 4) | $25,000 |
| `vip_investor_beta` | `password123` | VIP Accredited (risk 5) | $100,000 |

### Gamma Holdings Tenant

| Username | Password | Role | Balance |
|----------|----------|------|---------|
| `investor1_gamma` | `password123` | Regular (risk 3) | $10,000 |
| `investor2_gamma` | `password123` | Growth (risk 4) | $25,000 |
| `vip_investor_gamma` | `password123` | VIP Accredited (risk 5) | $100,000 |

---

## ABAC Rules

| Rule | Logic |
|------|-------|
| **Tenant Isolation** | `user.tenant_id == asset.tenant_id` |
| **Risk Check** | `user.risk_tolerance >= asset.risk_level` |
| **Accreditation** | If `asset.accreditation_required`, then `user.is_accredited` must be `true` |

---

## API Authentication

### Interactive Documentation (Swagger UI)
1. Navigate to `/api/docs`.
2. Click the **Authorize** button (indicated by the lock icon).
3. In the "Value" field, enter your access token.
   - *Note: You must first obtain a token via `POST /auth/token/` using valid credentials (e.g., `investor1_alpha` / `password123`).*

### CLI / Generic Usage
```bash
# Get JWT tokens
curl -X POST http://localhost:8000/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "investor1_alpha", "password": "password123"}'

# Response: {"access": "...", "refresh": "..."}

# Use access token
curl http://localhost:8000/api/v1/analytics/summary \
  -H "Authorization: Bearer <access_token>"
```

---

## Asset Categories (6 Types)

### 1. Real Estate
| Symbol | Name | Price | Risk | Image |
|--------|------|-------|------|-------|
| UTR | Urban Tower REIT | $150.00 | 2 | property 1.jpg |
| CPP | Coastal Properties | $85.50 | 3 | property 2.jpg |
| IPI | Industrial Parks Inc | $220.00 | 2 | property 3.jpg |

### 2. Tech Stocks
| Symbol | Name | Price | Risk | Accredited |
|--------|------|-------|------|------------|
| CLD | Cloud Dynamics | $1,250.00 | 4 | No |
| AII | AI Innovations | $890.00 | 5 | Yes |
| QCC | Quantum Computing Co | $340.00 | 5 | Yes |
| CSI | Cyber Shield Inc | $275.00 | 3 | No |
| GTS | Green Tech Solutions | $180.00 | 3 | No |

### 3. Commodities
| Symbol | Name | Price | Risk | Image |
|--------|------|-------|------|-------|
| GSF | Gold Standard Fund | $1,850.00 | 2 | gold.jpg |
| SST | Silver Stream | $24.50 | 3 | silver.jpg |
| REM | Rare Earth Minerals | $560.00 | 4 | coal pile.png |

### 4. Private Equity (Accredited Only)
| Symbol | Name | Price | Risk |
|--------|------|-------|------|
| VGF | Venture Growth Fund | $5,000.00 | 5 |
| BOP | Buyout Partners | $2,500.00 | 5 |
| GCL | Growth Capital LP | $3,500.00 | 5 |

### 5. Bonds (Low Risk)
| Symbol | Name | Price | Risk |
|--------|------|-------|------|
| TBF | US Treasury Bond Fund | $100.00 | 1 |
| UKG | UK Gilt Fund | $95.00 | 1 |
| GBE | German Bund ETF | $98.00 | 1 |

### 6. Collectibles (Accredited Only)
| Symbol | Name | Price | Risk |
|--------|------|-------|------|
| MAC | Modern Art Collection | $15,000.00 | 4 |
| VWF | Vintage Wine Fund | $8,500.00 | 4 |
| CCP | Classic Cars Portfolio | $25,000.00 | 5 |
