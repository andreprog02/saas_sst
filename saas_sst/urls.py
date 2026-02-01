from django.contrib import admin
from django.urls import path, include
from core.views import cadastro_view, dashboard_view
from django.contrib.auth import views as auth_views
from core.views import criar_setor # Adicione no import
from core.views import dashboard_view, cadastro_view, lista_funcionarios, criar_funcionario

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Rota de Login (Usa o padrão do Django)
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Rota de Cadastro (Novo Usuário)
    path('cadastrar/', cadastro_view, name='cadastro'),
    
    # Página Inicial (Dashboard)
    path('', dashboard_view, name='dashboard'),

    path('setores/novo/', criar_setor, name='criar_setor'),

    # ... as outras ...
    path('funcionarios/', lista_funcionarios, name='lista_funcionarios'),
    path('funcionarios/novo/', criar_funcionario, name='criar_funcionario'), # Nova rota



]