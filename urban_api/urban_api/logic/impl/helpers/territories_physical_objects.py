"""Territories physical objects internal logic is defined here."""

from fastapi import HTTPException
from geoalchemy2.functions import ST_AsGeoJSON
from sqlalchemy import cast, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncConnection

from urban_db.entities import (
    object_geometries_data,
    physical_object_types_dict,
    physical_objects_data,
    territories_data,
    urban_objects_data,
)
from urban_api.dto import PhysicalObjectDataDTO, PhysicalObjectWithGeometryDTO


async def get_physical_objects_by_territory_id_from_db(
    conn: AsyncConnection, territory_id: int, physical_object_type: int | None, name: str | None
) -> list[PhysicalObjectDataDTO]:
    """Get physical objects by territory id, optional physical object type."""

    statement = select(territories_data).where(territories_data.c.territory_id == territory_id)
    territory = (await conn.execute(statement)).one_or_none()
    if territory is None:
        raise HTTPException(status_code=404, detail="Given territory id is not found")

    statement = (
        select(
            physical_objects_data.c.physical_object_id,
            physical_objects_data.c.physical_object_type_id,
            physical_object_types_dict.c.name.label("physical_object_type_name"),
            physical_objects_data.c.name,
            object_geometries_data.c.address,
            physical_objects_data.c.properties,
        )
        .select_from(
            physical_objects_data.join(
                urban_objects_data,
                physical_objects_data.c.physical_object_id == urban_objects_data.c.physical_object_id,
            )
            .join(
                object_geometries_data,
                urban_objects_data.c.object_geometry_id == object_geometries_data.c.object_geometry_id,
            )
            .join(
                physical_object_types_dict,
                physical_objects_data.c.physical_object_type_id == physical_object_types_dict.c.physical_object_type_id,
            )
        )
        .where(object_geometries_data.c.territory_id == territory_id)
    )

    if physical_object_type is not None:
        statement = statement.where(physical_objects_data.c.physical_object_type_id == physical_object_type)
    if name is not None:
        statement = statement.where(physical_objects_data.c.name.ilike(f"%{name}%"))

    result = (await conn.execute(statement)).mappings().all()

    return [PhysicalObjectDataDTO(**physical_object) for physical_object in result]


async def get_physical_objects_with_geometry_by_territory_id_from_db(
    conn: AsyncConnection, territory_id: int, physical_object_type: int | None, name: str | None
) -> list[PhysicalObjectWithGeometryDTO]:
    """Get physical objects with geometry by territory id, optional physical object type."""

    statement = select(territories_data).where(territories_data.c.territory_id == territory_id)
    territory = (await conn.execute(statement)).one_or_none()
    if territory is None:
        raise HTTPException(status_code=404, detail="Given territory id is not found")

    statement = (
        select(
            physical_objects_data.c.physical_object_id,
            physical_objects_data.c.physical_object_type_id,
            physical_objects_data.c.name,
            object_geometries_data.c.address,
            physical_objects_data.c.properties,
            cast(ST_AsGeoJSON(object_geometries_data.c.geometry), JSONB).label("geometry"),
            cast(ST_AsGeoJSON(object_geometries_data.c.centre_point), JSONB).label("centre_point"),
        )
        .select_from(
            physical_objects_data.join(
                urban_objects_data,
                physical_objects_data.c.physical_object_id == urban_objects_data.c.physical_object_id,
            ).join(
                object_geometries_data,
                urban_objects_data.c.object_geometry_id == object_geometries_data.c.object_geometry_id,
            )
        )
        .where(object_geometries_data.c.territory_id == territory_id)
    )

    if physical_object_type is not None:
        statement = statement.where(physical_objects_data.c.physical_object_type_id == physical_object_type)
    if name is not None:
        statement = statement.where(physical_objects_data.c.name.ilike(f"%{name}%"))

    result = (await conn.execute(statement)).mappings().all()

    return [PhysicalObjectWithGeometryDTO(**physical_object) for physical_object in result]
