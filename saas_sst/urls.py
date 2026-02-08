from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from core.views import (
    dashboard, cadastro, lista_epis, novo_epi, editar_epi, deletar_epi,
    lista_funcionarios, novo_funcionario, editar_funcionario, detalhe_funcionario,
    lista_extintores, novo_extintor, editar_extintor, inspecao_extintor, mobile_scan, historico_extintor,
    lista_equipamentos, novo_equipamento, editar_equipamento, inspecao_equipamento, historico_equipamento,
    config_locais, config_tipos_epi,
    # Advertencias
    dashboard_advertencias, nova_advertencia, documento_advertencia, gerenciar_tipos_advertencia,
    # Configurações Gerais
    gerenciar_vacinas,
    # Quimicos
    dashboard_quimicos, novo_quimico, editar_quimico,
    # Hospitais
    dashboard_hospitais, novo_hospital, config_hospitais,
    # APIs para os Modais de EPI (Adicione estas linhas)
    api_criar_categoria_epi, api_criar_marca_epi, api_criar_tamanho_epi,
    entrada_estoque_epi
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Autenticação
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('cadastro/', cadastro, name='cadastro'),

    # Dashboard
    path('', dashboard, name='dashboard'),

    # EPIs
    path('estoque/', lista_epis, name='lista_epis'),
    path('estoque/novo/', novo_epi, name='novo_epi'),
    path('estoque/editar/<int:id>/', editar_epi, name='editar_epi'),
    path('estoque/deletar/<int:id>/', deletar_epi, name='deletar_epi'),
    path('estoque/entrada/<int:id>/', entrada_estoque_epi, name='entrada_estoque_epi'),

    # APIs JSON para Modais de EPI (Novas Rotas)
    path('api/epi/categoria/nova/', api_criar_categoria_epi, name='api_criar_categoria_epi'),
    path('api/epi/marca/nova/', api_criar_marca_epi, name='api_criar_marca_epi'),
    path('api/epi/tamanho/novo/', api_criar_tamanho_epi, name='api_criar_tamanho_epi'),

    # Configurações de EPI/Locais
    path('config/locais/', config_locais, name='config_locais'),
    path('config/tipos-epi/', config_tipos_epi, name='config_tipos_epi'),

    # Funcionários
    path('funcionarios/', lista_funcionarios, name='lista_funcionarios'),
    path('funcionarios/novo/', novo_funcionario, name='novo_funcionario'),
    path('funcionarios/editar/<int:id>/', editar_funcionario, name='editar_funcionario'),
    path('funcionarios/<int:id>/', detalhe_funcionario, name='detalhe_funcionario'),

    # Extintores
    path('extintores/', lista_extintores, name='lista_extintores'),
    path('extintores/novo/', novo_extintor, name='novo_extintor'),
    path('extintores/editar/<int:id>/', editar_extintor, name='editar_extintor'),
    path('extintores/inspecao/<int:id>/', inspecao_extintor, name='inspecao_extintor'),
    path('extintores/historico/<int:id>/', historico_extintor, name='historico_extintor'),
    path('mobile/scan/', mobile_scan, name='mobile_scan'),

    # Outros Equipamentos
    path('equipamentos/', lista_equipamentos, name='lista_equipamentos'),
    path('equipamentos/novo/', novo_equipamento, name='novo_equipamento'),
    path('equipamentos/editar/<int:id>/', editar_equipamento, name='editar_equipamento'),
    path('equipamentos/inspecao/<int:id>/', inspecao_equipamento, name='inspecao_equipamento'),
    path('equipamentos/historico/<int:id>/', historico_equipamento, name='historico_equipamento'),

    # Advertências
    path('advertencias/', dashboard_advertencias, name='dashboard_advertencias'),
    path('advertencias/nova/', nova_advertencia, name='nova_advertencia'),
    path('advertencias/documento/<int:adv_id>/', documento_advertencia, name='documento_advertencia'),
    path('advertencias/config/tipos/', gerenciar_tipos_advertencia, name='gerenciar_tipos_advertencia'),

    # Vacinas
    path('config/vacinas/', gerenciar_vacinas, name='gerenciar_vacinas'),

    # Produtos Químicos
    path('quimicos/', dashboard_quimicos, name='dashboard_quimicos'),
    path('quimicos/novo/', novo_quimico, name='novo_quimico'),
    path('quimicos/editar/<int:id>/', editar_quimico, name='editar_quimico'),

    # Hospitais
    path('hospitais/', dashboard_hospitais, name='dashboard_hospitais'),
    path('hospitais/novo/', novo_hospital, name='novo_hospital'),
    path('hospitais/config/', config_hospitais, name='config_hospitais'),
]