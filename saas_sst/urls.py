from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views

# IMPORTAÇÃO CORRETA DE TODAS AS VIEWS
from core.views import (
    cadastro_view, 
    dashboard_view, 
    criar_setor, 
    lista_funcionarios, 
    criar_funcionario,
    # Novas views importadas aqui:
    lista_epis, 
    criar_editar_epi, 
    deletar_epi, 
    gerenciar_tipos, 
    gerenciar_locais
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('cadastrar/', cadastro_view, name='cadastro'),
    path('', dashboard_view, name='dashboard'),
    
    path('setores/novo/', criar_setor, name='criar_setor'),
    path('funcionarios/', lista_funcionarios, name='lista_funcionarios'),
    path('funcionarios/novo/', criar_funcionario, name='criar_funcionario'),

    # ROTAS DE CONFIGURAÇÃO (Tipos e Locais)
    path('config/tipos-epi/', gerenciar_tipos, name='gerenciar_tipos'),
    path('config/locais/', gerenciar_locais, name='gerenciar_locais'),

    # ROTAS DE EPI (CRUD Completo)
    path('estoque/', lista_epis, name='lista_epis'),
    path('estoque/novo/', criar_editar_epi, name='criar_epi'),
    path('estoque/editar/<int:pk>/', criar_editar_epi, name='editar_epi'),
    path('estoque/deletar/<int:pk>/', deletar_epi, name='deletar_epi'),
]