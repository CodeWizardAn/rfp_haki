"""
Unit Tests for Database Operations
Tests for models, CRUD operations, and database manager
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestDatabaseManager:
    """Tests for DatabaseManager class"""
    
    def test_manager_creation(self, db_manager):
        """Test database manager is created successfully"""
        assert db_manager is not None
        assert db_manager.engine is not None
    
    def test_session_creation(self, db_manager):
        """Test session creation"""
        session = db_manager.get_session()
        assert session is not None
        session.close()
    
    def test_tables_created(self, db_manager):
        """Test that tables are created"""
        from sqlalchemy import inspect
        inspector = inspect(db_manager.engine)
        tables = inspector.get_table_names()
        assert len(tables) > 0
        # Check for expected tables
        assert any('product' in t.lower() for t in tables)


class TestOEMModel:
    """Tests for OEM model (must create OEM before Product)"""
    
    def test_create_oem(self, db_session):
        """Test creating an OEM"""
        from database.models import OEM
        
        oem = OEM(
            code="OEM001",
            name="Test OEM",
            full_name="Test OEM Manufacturing Ltd.",
            country="India",
            contact_email="test@oem.com",
            rating=4.5
        )
        
        db_session.add(oem)
        db_session.commit()
        
        assert oem.id is not None
        assert oem.code == "OEM001"
    
    def test_query_oem_by_code(self, db_session):
        """Test querying OEM by code"""
        from database.models import OEM
        
        # Create OEM
        oem = OEM(
            code="OEM002",
            name="Query Test OEM",
            country="India"
        )
        db_session.add(oem)
        db_session.commit()
        
        # Query
        queried = db_session.query(OEM).filter_by(code="OEM002").first()
        assert queried is not None
        assert queried.name == "Query Test OEM"


class TestProductModel:
    """Tests for Product model"""
    
    def test_create_product(self, db_session):
        """Test creating a product"""
        from database.models import Product, ProductStatus, OEM
        
        # First create an OEM (required foreign key)
        oem = OEM(code="PROD-OEM-001", name="Product Test OEM", country="India")
        db_session.add(oem)
        db_session.commit()
        
        # Now create product
        product = Product(
            sku="TEST-PROD-001",
            name="4 Core 25 sqmm XLPE Cable",
            description="Test cable product",
            oem_id=oem.id,
            category="Power Cables",
            product_type="XLPE Armoured",
            conductor_material="copper",
            conductor_size_sqmm=25.0,
            number_of_cores=4,
            insulation_type="XLPE",
            voltage_rating="1100V",
            unit_price=450.00,
            price_unit="per_meter",
            status=ProductStatus.ACTIVE
        )
        
        db_session.add(product)
        db_session.commit()
        
        assert product.id is not None
        assert product.sku == "TEST-PROD-001"
        assert product.conductor_size_sqmm == 25.0
    
    def test_query_product(self, db_session):
        """Test querying a product"""
        from database.models import Product, ProductStatus, OEM
        
        # Create OEM
        oem = OEM(code="QUERY-OEM-001", name="Query OEM", country="India")
        db_session.add(oem)
        db_session.commit()
        
        # Create product
        product = Product(
            sku="TEST-QUERY-001",
            name="Query Test Product",
            description="Test",
            oem_id=oem.id,
            category="Control Cables",
            conductor_material="copper",
            conductor_size_sqmm=4.0,
            number_of_cores=2,
            unit_price=100.00,
            status=ProductStatus.ACTIVE
        )
        db_session.add(product)
        db_session.commit()
        
        # Query
        queried = db_session.query(Product).filter_by(sku="TEST-QUERY-001").first()
        assert queried is not None
        assert queried.name == "Query Test Product"
        assert queried.oem.code == "QUERY-OEM-001"
    
    def test_update_product(self, db_session):
        """Test updating a product"""
        from database.models import Product, ProductStatus, OEM
        
        # Create OEM
        oem = OEM(code="UPDATE-OEM-001", name="Update OEM", country="India")
        db_session.add(oem)
        db_session.commit()
        
        # Create product
        product = Product(
            sku="TEST-UPDATE-001",
            name="Update Test",
            description="Original",
            oem_id=oem.id,
            category="Cables",
            unit_price=100.00,
            status=ProductStatus.ACTIVE
        )
        db_session.add(product)
        db_session.commit()
        
        # Update
        product.unit_price = 200.00
        product.conductor_size_sqmm = 16.0
        db_session.commit()
        
        # Verify
        updated = db_session.query(Product).filter_by(sku="TEST-UPDATE-001").first()
        assert updated.unit_price == 200.00
        assert updated.conductor_size_sqmm == 16.0
    
    def test_delete_product(self, db_session):
        """Test deleting a product"""
        from database.models import Product, ProductStatus, OEM
        
        # Create OEM
        oem = OEM(code="DELETE-OEM-001", name="Delete OEM", country="India")
        db_session.add(oem)
        db_session.commit()
        
        # Create product
        product = Product(
            sku="TEST-DELETE-001",
            name="Delete Test",
            description="To Delete",
            oem_id=oem.id,
            category="Cables",
            unit_price=100.00,
            status=ProductStatus.ACTIVE
        )
        db_session.add(product)
        db_session.commit()
        product_id = product.id
        
        # Delete
        db_session.delete(product)
        db_session.commit()
        
        # Verify
        deleted = db_session.query(Product).filter_by(id=product_id).first()
        assert deleted is None


class TestRFPModel:
    """Tests for RFP model"""
    
    def test_create_rfp(self, db_session):
        """Test creating an RFP"""
        from database.models import RFP, RFPStatus
        
        rfp = RFP(
            rfp_id="RFP-TEST-001",
            title="Test RFP",
            issuing_authority="Test Authority",
            published_date=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=30),
            status=RFPStatus.OPEN
        )
        
        db_session.add(rfp)
        db_session.commit()
        
        assert rfp.id is not None
        assert rfp.rfp_id == "RFP-TEST-001"
    
    def test_rfp_status_transitions(self, db_session):
        """Test RFP status changes"""
        from database.models import RFP, RFPStatus
        
        rfp = RFP(
            rfp_id="RFP-STATUS-001",
            title="Status Test RFP",
            issuing_authority="Test Authority",
            published_date=datetime.utcnow(),
            status=RFPStatus.DRAFT
        )
        db_session.add(rfp)
        db_session.commit()
        
        # Change status
        rfp.status = RFPStatus.OPEN
        db_session.commit()
        
        # Verify
        updated = db_session.query(RFP).filter_by(rfp_id="RFP-STATUS-001").first()
        assert updated.status == RFPStatus.OPEN


class TestProductRepository:
    """Tests for Product repository patterns"""
    
    def test_repository_create_product(self, db_session):
        """Test creating product using repository pattern"""
        from database.models import Product, OEM, ProductStatus
        
        # Create OEM
        oem = OEM(code="REPO-OEM-001", name="Repo OEM", country="India")
        db_session.add(oem)
        db_session.commit()
        
        # Create product
        product_data = {
            "sku": "REPO-PROD-001",
            "name": "Repository Test Product",
            "oem_id": oem.id,
            "category": "Test",
            "unit_price": 250.00,
            "status": ProductStatus.ACTIVE
        }
        product = Product(**product_data)
        db_session.add(product)
        db_session.commit()
        
        assert product.id is not None
    
    def test_repository_get_by_sku(self, db_session):
        """Test getting product by SKU"""
        from database.models import Product, OEM, ProductStatus
        
        # Create OEM and product
        oem = OEM(code="SKU-OEM-001", name="SKU OEM", country="India")
        db_session.add(oem)
        db_session.commit()
        
        product = Product(
            sku="SKU-PROD-001",
            name="SKU Test",
            oem_id=oem.id,
            unit_price=100.00,
            status=ProductStatus.ACTIVE
        )
        db_session.add(product)
        db_session.commit()
        
        # Get by SKU
        found = db_session.query(Product).filter_by(sku="SKU-PROD-001").first()
        assert found is not None
        assert found.name == "SKU Test"
    
    def test_repository_update_product(self, db_session):
        """Test updating product"""
        from database.models import Product, OEM, ProductStatus
        
        # Create OEM and product
        oem = OEM(code="UPD-OEM-001", name="Update OEM", country="India")
        db_session.add(oem)
        db_session.commit()
        
        product = Product(
            sku="UPD-PROD-001",
            name="Update Test",
            oem_id=oem.id,
            unit_price=100.00,
            status=ProductStatus.ACTIVE
        )
        db_session.add(product)
        db_session.commit()
        
        # Update
        product.unit_price = 150.00
        db_session.commit()
        
        # Verify
        updated = db_session.query(Product).filter_by(sku="UPD-PROD-001").first()
        assert updated.unit_price == 150.00
    
    def test_repository_delete_product(self, db_session):
        """Test deleting product"""
        from database.models import Product, OEM, ProductStatus
        
        # Create OEM and product
        oem = OEM(code="DEL-OEM-001", name="Delete OEM", country="India")
        db_session.add(oem)
        db_session.commit()
        
        product = Product(
            sku="DEL-PROD-001",
            name="Delete Test",
            oem_id=oem.id,
            unit_price=100.00,
            status=ProductStatus.ACTIVE
        )
        db_session.add(product)
        db_session.commit()
        product_id = product.id
        
        # Delete
        db_session.delete(product)
        db_session.commit()
        
        # Verify
        deleted = db_session.query(Product).filter_by(id=product_id).first()
        assert deleted is None


class TestDatabaseConstraints:
    """Tests for database constraints"""
    
    def test_unique_sku_constraint(self, db_session):
        """Test that SKU must be unique"""
        from database.models import Product, OEM, ProductStatus
        from sqlalchemy.exc import IntegrityError
        
        # Create OEM
        oem = OEM(code="CONST-OEM-001", name="Constraint OEM", country="India")
        db_session.add(oem)
        db_session.commit()
        
        # Create first product
        product1 = Product(
            sku="UNIQUE-SKU-001",
            name="First Product",
            oem_id=oem.id,
            unit_price=100.00,
            status=ProductStatus.ACTIVE
        )
        db_session.add(product1)
        db_session.commit()
        
        # Try to create second product with same SKU
        product2 = Product(
            sku="UNIQUE-SKU-001",
            name="Second Product",
            oem_id=oem.id,
            unit_price=200.00,
            status=ProductStatus.ACTIVE
        )
        db_session.add(product2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestDatabaseTransactions:
    """Tests for transaction handling"""
    
    def test_transaction_rollback(self, db_session):
        """Test transaction rollback on error"""
        from database.models import Product, OEM, ProductStatus
        
        # Create OEM
        oem = OEM(code="TRANS-OEM-001", name="Transaction OEM", country="India")
        db_session.add(oem)
        db_session.commit()
        
        # Create product
        product = Product(
            sku="TRANS-PROD-001",
            name="Transaction Test",
            oem_id=oem.id,
            unit_price=100.00,
            status=ProductStatus.ACTIVE
        )
        db_session.add(product)
        db_session.commit()
        original_price = product.unit_price
        
        # Try to update with invalid value
        try:
            product.unit_price = -100.00  # This should fail validation
            db_session.commit()
        except ValueError:
            db_session.rollback()
        
        # Verify rollback
        db_session.refresh(product)
        assert product.unit_price == original_price
    
    def test_bulk_insert(self, db_session):
        """Test bulk inserting products"""
        from database.models import Product, OEM, ProductStatus
        
        # Create OEM
        oem = OEM(code="BULK-OEM-001", name="Bulk OEM", country="India")
        db_session.add(oem)
        db_session.commit()
        
        # Create multiple products
        products = []
        for i in range(5):
            product = Product(
                sku=f"BULK-PROD-{i:03d}",
                name=f"Bulk Product {i}",
                oem_id=oem.id,
                unit_price=100.00 + i * 10,
                status=ProductStatus.ACTIVE
            )
            products.append(product)
        
        db_session.add_all(products)
        db_session.commit()
        
        # Verify
        count = db_session.query(Product).filter(Product.sku.like("BULK-PROD-%")).count()
        assert count == 5
