"""Fix enum type conversion

Revision ID: 5d6ecbcfefe6
Revises: 02e74ab3b348
Create Date: 2025-10-09 11:07:44.908137

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5d6ecbcfefe6'
down_revision = '02e74ab3b348'
branch_labels = None
depends_on = None


def upgrade():
    # Corrige conversão de enums no PostgreSQL
    
    # 1. Para tabela usuario - perfil_enum
    op.execute("ALTER TABLE usuario ALTER COLUMN perfil_enum TYPE perfilenum USING CASE "
               "WHEN perfil_enum::text = 'Administrador' THEN 'ADMIN'::perfilenum "
               "WHEN perfil_enum::text = 'Operador' THEN 'OPERADOR'::perfilenum "
               "WHEN perfil_enum::text = 'Monitor' THEN 'MONITOR'::perfilenum "
               "ELSE 'MONITOR'::perfilenum END")
    
    # 2. Para tabela usuario - status_enum
    op.execute("ALTER TABLE usuario ALTER COLUMN status_enum TYPE statusenum USING CASE "
               "WHEN status_enum::text = 'Ativo' THEN 'ATIVO'::statusenum "
               "WHEN status_enum::text = 'Inativo' THEN 'INATIVO'::statusenum "
               "ELSE 'ATIVO'::statusenum END")


def downgrade():
    # Reverter as conversões se necessário
    pass
