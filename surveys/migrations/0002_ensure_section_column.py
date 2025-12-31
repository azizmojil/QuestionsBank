from django.db import migrations


def ensure_section_column(apps, schema_editor):
    """
    Some databases may have been created before the section FK was introduced.
    Add the nullable section_id column if it is missing to prevent runtime errors.
    """
    connection = schema_editor.connection
    SurveyQuestion = apps.get_model("surveys", "SurveyQuestion")
    section_field = SurveyQuestion._meta.get_field("section")
    table_name = SurveyQuestion._meta.db_table
    column_name = section_field.column

    with connection.cursor() as cursor:
        columns = [
            col.name
            for col in connection.introspection.get_table_description(cursor, table_name)
        ]

    if column_name in columns:
        return

    _, _, args, kwargs = section_field.deconstruct()
    field = section_field.__class__(*args, **kwargs)
    field.set_attributes_from_name(section_field.name)
    schema_editor.add_field(SurveyQuestion, field)


class Migration(migrations.Migration):

    dependencies = [
        ("surveys", "0001_initial"),
    ]

    operations = [
        # Reverse is intentionally a noop; the base schema already includes this
        # column, and dropping it would make earlier migration states invalid.
        migrations.RunPython(ensure_section_column, migrations.RunPython.noop),
    ]
