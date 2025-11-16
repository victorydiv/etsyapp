# Pricing System Implementation Plan

## Overview
Add comprehensive pricing calculation system that accounts for all Etsy fees, material costs, and desired profit margins to help sellers price products profitably.

## Fee Structure (as of Nov 2025)

### One-Time Fees
- **Set-up fee**: $29.00 (one-time, already paid - can be amortized across products)

### Per-Listing Fees
- **Listing fee**: $0.20 per listing
- Charged when creating or renewing listings
- Converts from USD to shop currency

### Per-Transaction Fees
1. **Transaction fee**: 6.5% of order total (excluding tax)
2. **Payment processing fee**: 3% of order total (including tax + shipping) + $0.25
3. **Currency conversion fee**: 2.5% of sales funds (if shop currency ≠ payment account currency)
4. **Offsite Ads fee**: 12-15% of order total (optional, or required if >$10K sales in 12 months)

## Implementation Plan

### Phase 1: Database Schema Updates

Add to `database.py`:

```python
class ProductCost(Base):
    """Model for tracking product costs and pricing."""
    __tablename__ = 'product_costs'
    
    id = Column(Integer, primary_key=True)
    etsy_listing_id = Column(String, unique=True, index=True)
    
    # Material Costs
    material_cost = Column(Float, default=0.0)
    labor_cost = Column(Float, default=0.0)
    packaging_cost = Column(Float, default=0.0)
    shipping_supplies_cost = Column(Float, default=0.0)
    other_costs = Column(Float, default=0.0)
    
    # Pricing
    listed_price = Column(Float, default=0.0)
    shipping_charge = Column(Float, default=0.0)
    
    # Fee Settings
    include_offsite_ads = Column(Boolean, default=False)
    offsite_ads_rate = Column(Float, default=0.15)  # 15% default
    has_currency_conversion = Column(Boolean, default=False)
    
    # Calculated Fields (updated automatically)
    total_cost = Column(Float, default=0.0)
    total_fees = Column(Float, default=0.0)
    net_profit = Column(Float, default=0.0)
    profit_margin = Column(Float, default=0.0)  # percentage
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ShopSettings(Base):
    """Store shop-wide pricing settings."""
    __tablename__ = 'shop_settings'
    
    id = Column(Integer, primary_key=True)
    shop_id = Column(String, unique=True)
    
    # Amortized one-time costs
    setup_fee_paid = Column(Boolean, default=True)
    setup_fee_amount = Column(Float, default=29.00)
    estimated_annual_listings = Column(Integer, default=100)
    
    # Default pricing settings
    default_profit_margin_target = Column(Float, default=0.40)  # 40%
    default_labor_rate = Column(Float, default=15.00)  # per hour
    
    # Fee settings
    payment_processing_percent = Column(Float, default=0.03)  # 3%
    payment_processing_fixed = Column(Float, default=0.25)
    transaction_fee_percent = Column(Float, default=0.065)  # 6.5%
    listing_fee = Column(Float, default=0.20)
    currency_conversion_percent = Column(Float, default=0.025)  # 2.5%
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Phase 2: Pricing Calculator Module

Create `pricing_calculator.py`:

```python
class PricingCalculator:
    """Calculate optimal pricing considering all Etsy fees and costs."""
    
    def calculate_fees(self, listed_price: float, shipping_charge: float,
                      include_offsite_ads: bool = False,
                      has_currency_conversion: bool = False) -> dict:
        """
        Calculate all Etsy fees for a given price.
        
        Returns:
            dict with breakdown of all fees and net amount
        """
        
        # Listing fee (per listing, not per sale)
        listing_fee = 0.20
        
        # Transaction fee (6.5% of order total excluding tax)
        order_subtotal = listed_price
        transaction_fee = order_subtotal * 0.065
        
        # Payment processing fee (3% + $0.25 of total including shipping)
        order_total_with_shipping = listed_price + shipping_charge
        payment_processing_fee = (order_total_with_shipping * 0.03) + 0.25
        
        # Currency conversion fee (2.5% if applicable)
        currency_conversion_fee = 0
        if has_currency_conversion:
            currency_conversion_fee = order_total_with_shipping * 0.025
        
        # Offsite Ads fee (12-15% if applicable)
        offsite_ads_fee = 0
        if include_offsite_ads:
            offsite_ads_fee = order_subtotal * 0.15  # Using 15% (worst case)
        
        total_fees = (
            listing_fee + 
            transaction_fee + 
            payment_processing_fee + 
            currency_conversion_fee + 
            offsite_ads_fee
        )
        
        net_amount = order_total_with_shipping - total_fees
        
        return {
            'listed_price': listed_price,
            'shipping_charge': shipping_charge,
            'order_total': order_total_with_shipping,
            'fees': {
                'listing_fee': listing_fee,
                'transaction_fee': transaction_fee,
                'payment_processing_fee': payment_processing_fee,
                'currency_conversion_fee': currency_conversion_fee,
                'offsite_ads_fee': offsite_ads_fee,
                'total_fees': total_fees
            },
            'net_amount': net_amount,
            'effective_fee_rate': (total_fees / order_total_with_shipping) * 100
        }
    
    def calculate_minimum_price(self, total_cost: float, 
                               desired_profit_margin: float = 0.40,
                               shipping_charge: float = 0,
                               include_offsite_ads: bool = False,
                               has_currency_conversion: bool = False) -> dict:
        """
        Calculate minimum price needed to achieve desired profit margin.
        Uses iterative calculation since fees are based on price.
        """
        
        # Start with estimate
        estimated_price = total_cost / (1 - desired_profit_margin - 0.25)  # rough estimate
        
        # Iterate to find exact price
        for _ in range(10):  # Should converge quickly
            fees = self.calculate_fees(
                estimated_price, 
                shipping_charge,
                include_offsite_ads,
                has_currency_conversion
            )
            
            net_needed = total_cost / (1 - desired_profit_margin)
            price_needed = net_needed + fees['fees']['total_fees'] - shipping_charge
            
            if abs(price_needed - estimated_price) < 0.01:
                break
            
            estimated_price = price_needed
        
        final_fees = self.calculate_fees(
            estimated_price,
            shipping_charge,
            include_offsite_ads,
            has_currency_conversion
        )
        
        actual_profit = final_fees['net_amount'] - total_cost
        actual_margin = (actual_profit / final_fees['net_amount']) * 100
        
        return {
            'recommended_price': round(estimated_price, 2),
            'shipping_charge': shipping_charge,
            'total_cost': total_cost,
            'total_fees': final_fees['fees']['total_fees'],
            'net_amount': final_fees['net_amount'],
            'profit': actual_profit,
            'profit_margin': actual_margin,
            'fee_breakdown': final_fees['fees']
        }
    
    def compare_scenarios(self, total_cost: float, price: float,
                         shipping_charge: float = 0) -> dict:
        """
        Compare different fee scenarios (with/without offsite ads, etc.)
        """
        
        scenarios = {}
        
        # Scenario 1: Basic (no offsite ads, no currency conversion)
        scenarios['basic'] = self.calculate_fees(price, shipping_charge, False, False)
        scenarios['basic']['scenario_name'] = 'Basic (no optional fees)'
        
        # Scenario 2: With offsite ads
        scenarios['with_ads'] = self.calculate_fees(price, shipping_charge, True, False)
        scenarios['with_ads']['scenario_name'] = 'With Offsite Ads (15%)'
        
        # Scenario 3: With currency conversion
        scenarios['with_conversion'] = self.calculate_fees(price, shipping_charge, False, True)
        scenarios['with_conversion']['scenario_name'] = 'With Currency Conversion'
        
        # Scenario 4: Worst case (all fees)
        scenarios['worst_case'] = self.calculate_fees(price, shipping_charge, True, True)
        scenarios['worst_case']['scenario_name'] = 'Worst Case (all fees)'
        
        # Add profit calculations
        for scenario in scenarios.values():
            profit = scenario['net_amount'] - total_cost
            scenario['profit'] = profit
            scenario['profit_margin'] = (profit / scenario['net_amount'] * 100) if scenario['net_amount'] > 0 else 0
        
        return scenarios
```

### Phase 3: UI Additions to main.py

Add new menu section:

```
📊 PRICING & PROFITABILITY
  17. Calculate optimal pricing
  18. Analyze product profitability
  19. Compare pricing scenarios
  20. Set cost breakdown for product
  21. View profit margins report
```

### Phase 4: Features to Implement

1. **Cost Entry Interface**
   - Enter material costs per product
   - Track labor time and calculate cost
   - Add packaging and shipping supply costs
   - Save cost data to database

2. **Price Calculator**
   - Input total costs
   - Set desired profit margin
   - Calculate recommended price
   - Show fee breakdown

3. **Profitability Analysis**
   - Show actual profit per product
   - Compare expected vs actual margins
   - Identify underpriced items
   - Generate profitability reports

4. **Scenario Comparison**
   - Show net profit with/without offsite ads
   - Calculate impact of currency conversion
   - Help decide if offsite ads are worth it

5. **Bulk Operations**
   - Analyze profitability of all products
   - Suggest price adjustments
   - Export pricing reports to CSV

### Phase 5: Reporting Features

```python
# Reports to add:
- Profitability by product
- Total fees paid (monthly/yearly)
- Average profit margin across all products
- Products below target margin
- ROI on setup fee
- Fee breakdown analysis
```

## User Workflow Examples

### Example 1: Setting up a new product
1. Enter material costs ($15)
2. Enter labor time (2 hours @ $15/hr = $30)
3. Enter packaging ($2)
4. Total cost: $47
5. Set target margin: 40%
6. Calculator recommends: $89.99
7. System shows: "Net profit: $18.80, Margin: 40.1%"

### Example 2: Analyzing existing product
1. Select product from inventory
2. Enter actual costs if not already set
3. System shows current price: $75
4. System calculates actual profit: $12.50
5. System warns: "Below target margin! Consider pricing at $89.99"

### Example 3: Comparing scenarios
1. Enter product with $50 cost, $100 price
2. System shows:
   - Without offsite ads: $25 profit (25% margin)
   - With offsite ads: $10 profit (10% margin)
   - Recommendation: "Avoid offsite ads unless needed for visibility"

## Data Migration

When implementing, need to:
1. Add new tables to database
2. Prompt users to enter cost data for existing inventory
3. Provide import from CSV option
4. Set default shop settings

## Configuration

Add to `.env`:
```
# Pricing Settings
DEFAULT_PROFIT_MARGIN=0.40
DEFAULT_LABOR_RATE=15.00
INCLUDE_OFFSITE_ADS=false
HAS_CURRENCY_CONVERSION=false
```

## Future Enhancements

- Track fee changes over time
- Calculate break-even points
- Suggest optimal pricing tiers
- A/B testing price points
- Seasonal pricing adjustments
- Bulk discount calculations
- Bundle pricing optimizer

## Testing Plan

1. Unit tests for fee calculations
2. Verify against actual Etsy fee examples
3. Test edge cases (very low/high prices)
4. Validate iterative solver convergence
5. Test with real product data

---

**Status**: Planned for future implementation
**Priority**: High - critical for profitability
**Estimated effort**: 2-3 days development
**Dependencies**: Current inventory system must be in place
