from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.store import Product
from app.schemas.store import ProductCreate, ProductUpdate, ProductResponse
from app.utils.auth import get_current_user

router = APIRouter(prefix="/store", tags=["Store"])

@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_in: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new product listing. Restricted to Pastor or Admin role.
    Products are permanently bound to the user's church.
    """
    # Enforce admin / pastor role (Assuming role 'admin' or 'pastor')
    if current_user.role not in ["admin", "pastor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admins and Pastors can create store items."
        )

    if not current_user.church_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must belong to a church to create products."
        )

    new_product = Product(
        **product_in.model_dump(),
        church_id=current_user.church_id
    )
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    
    return new_product


@router.get("/products", response_model=List[ProductResponse])
async def get_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all active products for the current user's church.
    """
    if not current_user.church_id:
        return []

    stmt = select(Product).filter(
        Product.church_id == current_user.church_id,
        Product.is_active == True
    ).order_by(Product.created_at.desc())

    result = await db.execute(stmt)
    products = result.scalars().all()
    return products


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve details of a single product. 
    It must belong to the user's church.
    """
    if not current_user.church_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must belong to a church to view products."
        )

    stmt = select(Product).filter(
        Product.id == product_id,
        Product.church_id == current_user.church_id
    )
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    return product


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_in: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a product. Restricted to Pastor or Admin role.
    """
    if current_user.role not in ["admin", "pastor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admins and Pastors can edit store items."
        )

    stmt = select(Product).filter(
        Product.id == product_id,
        Product.church_id == current_user.church_id
    )
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    update_data = product_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)
    
    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a product (deactivates it). Restricted to Pastor or Admin role.
    """
    if current_user.role not in ["admin", "pastor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admins and Pastors can delete store items."
        )

    stmt = select(Product).filter(
        Product.id == product_id,
        Product.church_id == current_user.church_id
    )
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Soft delete
    product.is_active = False
    await db.commit()
    
    return None
