"""
Base repository with common database operations.
"""

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from undertow.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Base repository providing common CRUD operations.

    All repositories should inherit from this class.

    Example:
        class UserRepository(BaseRepository[User]):
            model = User
    """

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository.

        Args:
            session: Database session
        """
        self.session = session

    async def get(self, id: str | UUID) -> ModelT | None:
        """
        Get entity by ID.

        Args:
            id: Entity ID

        Returns:
            Entity or None if not found
        """
        return await self.session.get(self.model, str(id))

    async def get_by_ids(self, ids: list[str]) -> list[ModelT]:
        """
        Get multiple entities by IDs.

        Args:
            ids: List of entity IDs

        Returns:
            List of found entities
        """
        if not ids:
            return []

        query = select(self.model).where(self.model.id.in_(ids))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list(
        self,
        offset: int = 0,
        limit: int = 50,
        order_by: Any = None,
    ) -> list[ModelT]:
        """
        List entities with pagination.

        Args:
            offset: Number of records to skip
            limit: Maximum records to return
            order_by: Column to order by

        Returns:
            List of entities
        """
        query = select(self.model)

        if order_by is not None:
            query = query.order_by(order_by)

        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self) -> int:
        """
        Count total entities.

        Returns:
            Total count
        """
        query = select(func.count()).select_from(self.model)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def create(self, entity: ModelT) -> ModelT:
        """
        Create a new entity.

        Args:
            entity: Entity to create

        Returns:
            Created entity with ID
        """
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def create_many(self, entities: list[ModelT]) -> list[ModelT]:
        """
        Create multiple entities.

        Args:
            entities: Entities to create

        Returns:
            Created entities
        """
        self.session.add_all(entities)
        await self.session.flush()
        for entity in entities:
            await self.session.refresh(entity)
        return entities

    async def update(self, entity: ModelT) -> ModelT:
        """
        Update an entity.

        Args:
            entity: Entity with updated values

        Returns:
            Updated entity
        """
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, id: str | UUID) -> bool:
        """
        Delete entity by ID.

        Args:
            id: Entity ID

        Returns:
            True if deleted
        """
        entity = await self.get(id)
        if entity:
            await self.session.delete(entity)
            await self.session.flush()
            return True
        return False

    async def delete_many(self, ids: list[str]) -> int:
        """
        Delete multiple entities.

        Args:
            ids: Entity IDs to delete

        Returns:
            Number of deleted entities
        """
        if not ids:
            return 0

        query = delete(self.model).where(self.model.id.in_(ids))
        result = await self.session.execute(query)
        await self.session.flush()
        return result.rowcount

    async def exists(self, id: str | UUID) -> bool:
        """
        Check if entity exists.

        Args:
            id: Entity ID

        Returns:
            True if exists
        """
        query = select(func.count()).select_from(self.model).where(
            self.model.id == str(id)
        )
        result = await self.session.execute(query)
        return (result.scalar() or 0) > 0

