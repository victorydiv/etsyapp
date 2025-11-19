"""Customer management module."""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from database import Customer, get_db


class CustomerManager:
    """Manages customer operations."""
    
    def __init__(self):
        pass
    
    def search_customers(self, search_term: str, db: Session = None) -> List[Customer]:
        """Search customers by name, email, or phone."""
        close_db = False
        if db is None:
            db = get_db()
            close_db = True
        
        try:
            search_pattern = f"%{search_term}%"
            customers = db.query(Customer).filter(
                (Customer.name.ilike(search_pattern)) |
                (Customer.email.ilike(search_pattern)) |
                (Customer.phone.ilike(search_pattern))
            ).filter(Customer.is_active == True).all()
            
            return customers
        finally:
            if close_db:
                db.close()
    
    def get_customer(self, customer_id: int, db: Session = None) -> Optional[Customer]:
        """Get customer by ID."""
        close_db = False
        if db is None:
            db = get_db()
            close_db = True
        
        try:
            return db.query(Customer).filter(Customer.id == customer_id).first()
        finally:
            if close_db:
                db.close()
    
    def create_customer(self, name: str, email: str = None, phone: str = None,
                       address_line1: str = None, address_line2: str = None,
                       city: str = None, state: str = None, postal_code: str = None,
                       country: str = 'US', notes: str = None,
                       db: Session = None) -> Customer:
        """Create a new customer."""
        close_db = False
        if db is None:
            db = get_db()
            close_db = True
        
        try:
            customer = Customer(
                name=name,
                email=email,
                phone=phone,
                address_line1=address_line1,
                address_line2=address_line2,
                city=city,
                state=state,
                postal_code=postal_code,
                country=country,
                notes=notes
            )
            db.add(customer)
            db.commit()
            db.refresh(customer)
            return customer
        finally:
            if close_db:
                db.close()
    
    def update_customer(self, customer_id: int, **kwargs) -> bool:
        """Update customer information."""
        db = get_db()
        try:
            customer = db.query(Customer).filter(Customer.id == customer_id).first()
            if not customer:
                return False
            
            for key, value in kwargs.items():
                if hasattr(customer, key):
                    setattr(customer, key, value)
            
            db.commit()
            return True
        finally:
            db.close()
    
    def get_all_customers(self, active_only: bool = True, db: Session = None) -> List[Customer]:
        """Get all customers."""
        close_db = False
        if db is None:
            db = get_db()
            close_db = True
        
        try:
            query = db.query(Customer)
            if active_only:
                query = query.filter(Customer.is_active == True)
            return query.order_by(Customer.name).all()
        finally:
            if close_db:
                db.close()
    
    def get_customer_formatted_address(self, customer: Customer) -> str:
        """Get formatted shipping address for customer."""
        parts = []
        if customer.address_line1:
            parts.append(customer.address_line1)
        if customer.address_line2:
            parts.append(customer.address_line2)
        
        city_line = []
        if customer.city:
            city_line.append(customer.city)
        if customer.state:
            city_line.append(customer.state)
        if customer.postal_code:
            city_line.append(customer.postal_code)
        if city_line:
            parts.append(', '.join(city_line))
        
        if customer.country and customer.country != 'US':
            parts.append(customer.country)
        
        return '\n'.join(parts)
