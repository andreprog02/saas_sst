from django.contrib import admin
from django.urls import path
from core import views
from django.contrib.auth import views as auth_views
from core.views import (
    dashboard, cadastro, 
    # EPIs
    lista_epis, novo_epi, editar_epi, deletar_epi, entrada_estoque_epi,
    # Config EPIs
    config_locais, config_tipos_epi,
    # APIs EPIs
    api_criar_categoria_epi, api_criar_marca_epi, api_criar_tamanho_epi,
    # Funcionários
    lista_funcionarios, novo_funcionario, editar_funcionario, detalhe_funcionario,
    # Ações do Prontuário (Faltavam estes imports)
    registrar_vacina, registrar_entrega_epi, registrar_treinamento, 
    registrar_afastamento, registrar_acidente, registrar_advertencia_modal,
    # Extintores
    lista_extintores, novo_extintor, editar_extintor, inspecao_extintor, mobile_scan, historico_extintor,
    # Equipamentos
    lista_equipamentos, novo_equipamento, editar_equipamento, inspecao_equipamento, historico_equipamento,
    # Setores
    criar_setor,
    # Advertencias
    dashboard_advertencias, nova_advertencia, documento_advertencia, gerenciar_tipos_advertencia,
    # Configurações Gerais
    gerenciar_vacinas,
    # Quimicos
    dashboard_quimicos, novo_quimico, editar_quimico, deletar_quimico,
    # Hospitais
    dashboard_hospitais, novo_hospital, config_hospitais,
    # API Hospital
    api_criar_especialidade,
    criar_risco, deletar_risco, associar_risco_setor
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Autenticação
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('cadastro/', cadastro, name='cadastro'),

    # Dashboard
    path('', dashboard, name='dashboard'),

    # Setores
    path('setor/novo/', criar_setor, name='criar_setor'),

    # EPIs
    path('estoque/', lista_epis, name='lista_epis'),
    path('estoque/novo/', novo_epi, name='novo_epi'),
    path('estoque/editar/<int:id>/', editar_epi, name='editar_epi'),
    path('estoque/deletar/<int:id>/', deletar_epi, name='deletar_epi'),
    path('estoque/entrada/<int:id>/', entrada_estoque_epi, name='entrada_estoque_epi'),

    # APIs JSON para Modais de EPI
    path('api/epi/categoria/nova/', api_criar_categoria_epi, name='api_criar_categoria_epi'),
    path('api/epi/marca/nova/', api_criar_marca_epi, name='api_criar_marca_epi'),
    path('api/epi/tamanho/novo/', api_criar_tamanho_epi, name='api_criar_tamanho_epi'),

    # Configurações de EPI/Locais
    path('config/locais/', config_locais, name='config_locais'),
    path('config/tipos-epi/', config_tipos_epi, name='config_tipos_epi'),

    # Funcionários e Prontuário
    path('funcionarios/', lista_funcionarios, name='lista_funcionarios'),
    path('funcionarios/novo/', novo_funcionario, name='novo_funcionario'),
    path('funcionarios/editar/<int:id>/', editar_funcionario, name='editar_funcionario'),
    path('funcionarios/<int:id>/', detalhe_funcionario, name='detalhe_funcionario'),
    
    # Rotas de Ação do Prontuário (Registro Rápido)
    path('funcionarios/<int:func_id>/vacina/', registrar_vacina, name='registrar_vacina'),
    path('funcionarios/<int:func_id>/epi/', registrar_entrega_epi, name='registrar_entrega_epi'),
    path('funcionarios/<int:func_id>/treinamento/', registrar_treinamento, name='registrar_treinamento'),
    path('funcionarios/<int:func_id>/afastamento/', registrar_afastamento, name='registrar_afastamento'),
    path('funcionarios/<int:func_id>/acidente/', registrar_acidente, name='registrar_acidente'),
    path('funcionarios/<int:func_id>/advertencia/', registrar_advertencia_modal, name='registrar_advertencia_modal'),

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

    # Advertências (Gestão)
    path('advertencias/', dashboard_advertencias, name='dashboard_advertencias'),
    path('advertencias/nova/', nova_advertencia, name='nova_advertencia'),
    path('advertencias/documento/<int:adv_id>/', documento_advertencia, name='documento_advertencia'),
    path('advertencias/config/tipos/', gerenciar_tipos_advertencia, name='gerenciar_tipos_advertencia'),

    # Vacinas (Configuração)
    path('config/vacinas/', gerenciar_vacinas, name='gerenciar_vacinas'),
    path('config/vacinas/popular/', views.popular_vacinas, name='popular_vacinas'), # <--- NOVA ROTA

    # Produtos Químicos
    path('quimicos/', dashboard_quimicos, name='dashboard_quimicos'),
    path('quimicos/novo/', novo_quimico, name='novo_quimico'),
    path('quimicos/editar/<int:id>/', editar_quimico, name='editar_quimico'),
    path('quimicos/deletar/<int:pk>/', deletar_quimico, name='deletar_quimico'),

    # Novas Rotas de Risco Ocupacional e Mapa
    path('riscos/novo/', criar_risco, name='criar_risco'),
    path('riscos/deletar/<int:id>/', deletar_risco, name='deletar_risco'),
    path('setor/<int:setor_id>/associar-riscos/', associar_risco_setor, name='associar_risco_setor'),

    # Hospitais
    path('hospitais/', dashboard_hospitais, name='dashboard_hospitais'),
    path('hospitais/novo/', novo_hospital, name='novo_hospital'),
    path('hospitais/config/', config_hospitais, name='config_hospitais'),
    
    # API Hospital
    path('api/especialidades/nova/', api_criar_especialidade, name='api_criar_especialidade'),

    path('api/quimicos/', views.api_lista_quimicos, name='api_lista_quimicos'),

    path('funcionarios/<int:func_id>/exames/novo/', views.registrar_exame, name='registrar_exame'),
    path('exames/deletar/<int:exame_id>/', views.deletar_exame, name='deletar_exame'),
    # ----------------------------------


    path('configuracoes/setores/', views.lista_setores, name='lista_setores'),
    path('configuracoes/setores/novo/', views.novo_setor, name='novo_setor'),
    path('configuracoes/setores/editar/<int:id>/', views.editar_setor, name='editar_setor'),
    path('configuracoes/setores/deletar/<int:id>/', views.deletar_setor, name='deletar_setor'),

    # ADVERTÊNCIAS
    path('advertencias/', views.lista_advertencias, name='lista_advertencias'),
    # path('advertencias/nova/', views.nova_advertencia, name='nova_advertencia'),



    # --- MÓDULO: PMOC (Ar Condicionado) - NOVO ---
    path('pmoc/', views.lista_pmoc, name='lista_pmoc'),
    path('pmoc/novo/', views.novo_pmoc, name='novo_pmoc'),
    # path('pmoc/editar/<int:pk>/', views.editar_pmoc, name='editar_pmoc'), # Futuro

    # --- MÓDULO: NR-13 (Caldeiras e Vasos) - NOVO ---
    path('nr13/', views.lista_nr13, name='lista_nr13'),
    path('nr13/novo/', views.novo_nr13, name='novo_nr13'),
    # path('nr13/editar/<int:pk>/', views.editar_nr13, name='editar_nr13'), # Futuro


    path('exames/editar/<int:exame_id>/', views.editar_exame, name='editar_exame'),
]