{#
    Sem este override, o dbt concatena o schema do perfil com o schema do
    modelo e a camada gold viraria "main_gold". Aqui o schema configurado no
    modelo vale como nome final, entao o banco fica com bronze, silver e gold
    limpos — que e o que aparece na documentacao e no grafo de linhagem.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}
    {%- if custom_schema_name is none -%}
        {{ default_schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
