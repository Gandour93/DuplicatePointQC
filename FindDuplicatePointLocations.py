import arcpy
from collections import defaultdict
import os


def main():

    # ---------------------------------------------------------
    # 1. Get parameters
    # ---------------------------------------------------------
    input_features = arcpy.GetParameterAsText(0)
    output_features = arcpy.GetParameterAsText(1)

    arcpy.AddMessage("==============================================")
    arcpy.AddMessage("Duplicate Point Location QC")
    arcpy.AddMessage("==============================================")

    # ---------------------------------------------------------
    # 2. Check input geometry type
    # ---------------------------------------------------------
    input_desc = arcpy.Describe(input_features)

    if input_desc.shapeType.upper() != "POINT":
        raise arcpy.ExecuteError(
            "The input dataset must be a Point Feature Class."
        )

    arcpy.AddMessage("Input geometry type: Point")

    # ---------------------------------------------------------
    # 3. Count input records
    # ---------------------------------------------------------
    input_count = int(
        arcpy.management.GetCount(input_features)[0]
    )

    arcpy.AddMessage(
        f"Input records: {input_count}"
    )

    if input_count == 0:
        raise arcpy.ExecuteError(
            "The input Point Feature Class contains no records."
        )

    # ---------------------------------------------------------
    # 4. Group points by exact X,Y coordinates
    # ---------------------------------------------------------
    coordinate_groups = defaultdict(list)

    empty_geometry_count = 0

    with arcpy.da.SearchCursor(
        input_features,
        ["OID@", "SHAPE@XY"]
    ) as cursor:

        for oid, xy in cursor:

            if xy is None:
                empty_geometry_count += 1
                continue

            x, y = xy

            coordinate_groups[(x, y)].append(oid)

    # ---------------------------------------------------------
    # 5. Report empty geometries
    # ---------------------------------------------------------
    if empty_geometry_count > 0:

        arcpy.AddWarning(
            f"Empty geometries skipped: {empty_geometry_count}"
        )

    # ---------------------------------------------------------
    # 6. Keep only duplicated locations
    # ---------------------------------------------------------
    duplicate_groups = {
        coordinates: oids
        for coordinates, oids in coordinate_groups.items()
        if len(oids) > 1
    }

    duplicate_location_count = len(duplicate_groups)

    duplicate_record_count = sum(
        len(oids)
        for oids in duplicate_groups.values()
    )

    # ---------------------------------------------------------
    # 7. Report duplicate statistics
    # ---------------------------------------------------------
    arcpy.AddMessage(
        f"Unique locations checked: {len(coordinate_groups)}"
    )

    arcpy.AddMessage(
        f"Duplicate locations found: {duplicate_location_count}"
    )

    arcpy.AddMessage(
        f"Records involved in duplicates: {duplicate_record_count}"
    )

    # ---------------------------------------------------------
    # 8. Check whether duplicates exist
    # ---------------------------------------------------------
    if duplicate_location_count == 0:

        arcpy.AddWarning(
            "No duplicate point locations were found."
        )

    # ---------------------------------------------------------
    # 9. Get spatial reference
    # ---------------------------------------------------------
    spatial_reference = input_desc.spatialReference

    # ---------------------------------------------------------
    # 10. Get output workspace and name
    # ---------------------------------------------------------
    output_workspace = os.path.dirname(output_features)
    output_name = os.path.basename(output_features)

    # ---------------------------------------------------------
    # 11. Delete existing output if necessary
    # ---------------------------------------------------------
    if arcpy.Exists(output_features):

        arcpy.AddMessage(
            "Existing output found. It will be replaced."
        )

        arcpy.management.Delete(output_features)

    # ---------------------------------------------------------
    # 12. Create output Point Feature Class
    # ---------------------------------------------------------
    arcpy.management.CreateFeatureclass(
        output_workspace,
        output_name,
        "POINT",
        spatial_reference=spatial_reference
    )

    # ---------------------------------------------------------
    # 13. Add fields
    # ---------------------------------------------------------
    arcpy.management.AddField(
        output_features,
        "Duplicate_ID",
        "LONG",
        field_alias="Duplicate ID"
    )

    arcpy.management.AddField(
        output_features,
        "X_Coord",
        "DOUBLE",
        field_alias="X Coordinate"
    )

    arcpy.management.AddField(
        output_features,
        "Y_Coord",
        "DOUBLE",
        field_alias="Y Coordinate"
    )

    arcpy.management.AddField(
        output_features,
        "Duplicate_Count",
        "LONG",
        field_alias="Duplicate Count"
    )

    # ---------------------------------------------------------
    # 14. Write duplicate locations
    # ---------------------------------------------------------
    duplicate_id = 1

    with arcpy.da.InsertCursor(
        output_features,
        [
            "SHAPE@XY",
            "Duplicate_ID",
            "X_Coord",
            "Y_Coord",
            "Duplicate_Count"
        ]
    ) as cursor:

        for (x, y), oids in duplicate_groups.items():

            cursor.insertRow(
                [
                    (x, y),
                    duplicate_id,
                    x,
                    y,
                    len(oids)
                ]
            )

            duplicate_id += 1

    # ---------------------------------------------------------
    # 15. Final report
    # ---------------------------------------------------------
    arcpy.AddMessage("==============================================")
    arcpy.AddMessage("QC completed successfully.")
    arcpy.AddMessage(
        f"Duplicate locations: {duplicate_location_count}"
    )
    arcpy.AddMessage(
        f"Duplicate records: {duplicate_record_count}"
    )
    arcpy.AddMessage("==============================================")


if __name__ == "__main__":
    main()