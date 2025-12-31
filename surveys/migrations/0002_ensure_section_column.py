from django.db import migrations


def ensure_section_column(apps, schema_editor):
    """
    Some databases may have been created before the section FK was introduced.
    Add the nullable section_id column if it is missing to prevent runtime errors.
    """
    connection = schema_editor.connection
    table_name = "surveys_surveyquestion"
    column_name = "section_id"

    with connection.cursor() as cursor:
        columns = [
            col.name
            for col in connection.introspection.get_table_description(cursor, table_name)
        ]

    if column_name in columns:
        return

    quoted_table = connection.ops.quote_name(table_name)
    quoted_column = connection.ops.quote_name(column_name)

    schema_editor.execute(
        f"ALTER TABLE {quoted_table} ADD COLUMN {quoted_column} integer NULL"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("surveys", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(ensure_section_column, migrations.RunPython.noop),
    ]
