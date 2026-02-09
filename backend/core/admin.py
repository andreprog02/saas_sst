from django.contrib import admin
from .models import (
    Empresa, PerfilUsuario, Funcionario, 
    ProdutoQuimico, Localizacao, Setor
)

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nome_fantasia', 'cnpj', 'ativo')

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'empresa', 'is_admin')

@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cargo', 'empresa')

@admin.register(ProdutoQuimico)
class ProdutoQuimicoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'fabricante', 'empresa')

# Registrando outros modelos úteis
admin.site.register(Localizacao)
admin.site.register(Setor)