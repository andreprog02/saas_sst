from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

from core.views import (
    # Views Gerais
    cadastro_view, dashboard_view, criar_setor, 
    
    # Funcionários e Prontuário
    lista_funcionarios, criar_funcionario, editar_funcionario,
    detalhe_funcionario, adicionar_vacina_func, adicionar_epi_func, 
    adicionar_treinamento_func, adicionar_advertencia_func,
    adicionar_afastamento_func, adicionar_acidente_func,
    
    # EPIs (Estoque)
    lista_epis, criar_editar_epi, deletar_epi, 
    
    # Configurações Gerais
    gerenciar_tipos, gerenciar_locais, gerenciar_vacinas,
    
    # Advertências
    gerenciar_tipos_advertencia, nova_advertencia, 
    dashboard_advertencias, imprimir_advertencia,
    
    # Extintores
    dashboard_extintores, criar_editar_extintor, 
    registrar_inspecao, historico_extintor, 
    exportar_extintores, gerar_qrcode, imprimir_etiqueta, extintor_mobile,

    # Outros Equipamentos
    dashboard_equipamentos, criar_editar_equipamento, 
    inspecionar_equipamento, historico_equipamento,

    # Produtos Químicos
    dashboard_quimicos, criar_editar_quimico, deletar_quimico,

    # Hospitais e Emergências (NOVOS)
    dashboard_hospitais, criar_editar_hospital, gerenciar_especialidades,
    api_criar_especialidade
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Autenticação
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Core
    path('cadastrar/', cadastro_view, name='cadastro'),
    path('', dashboard_view, name='dashboard'),
    path('setores/novo/', criar_setor, name='criar_setor'),
    
    # --- FUNCIONÁRIOS ---
    path('funcionarios/', lista_funcionarios, name='lista_funcionarios'),
    path('funcionarios/novo/', criar_funcionario, name='criar_funcionario'),
    path('funcionarios/editar/<int:pk>/', editar_funcionario, name='editar_funcionario'),
    path('funcionarios/<int:pk>/', detalhe_funcionario, name='detalhe_funcionario'),
    
    # Ações do Prontuário
    path('funcionarios/<int:func_id>/vacina/nova/', adicionar_vacina_func, name='adicionar_vacina_func'),
    path('funcionarios/<int:func_id>/epi/novo/', adicionar_epi_func, name='adicionar_epi_func'),
    path('funcionarios/<int:func_id>/treinamento/novo/', adicionar_treinamento_func, name='adicionar_treinamento_func'),
    path('funcionarios/<int:func_id>/advertencia/nova/', adicionar_advertencia_func, name='adicionar_advertencia_func'),
    path('funcionarios/<int:func_id>/afastamento/novo/', adicionar_afastamento_func, name='adicionar_afastamento_func'),
    path('funcionarios/<int:func_id>/acidente/novo/', adicionar_acidente_func, name='adicionar_acidente_func'),

    # --- CONFIGURAÇÕES ---
    path('config/tipos-epi/', gerenciar_tipos, name='gerenciar_tipos'),
    path('config/locais/', gerenciar_locais, name='gerenciar_locais'),
    path('config/vacinas/', gerenciar_vacinas, name='gerenciar_vacinas'),

    # --- ESTOQUE EPI ---
    path('estoque/', lista_epis, name='lista_epis'),
    path('estoque/novo/', criar_editar_epi, name='criar_epi'),
    path('estoque/editar/<int:pk>/', criar_editar_epi, name='editar_epi'),
    path('estoque/deletar/<int:pk>/', deletar_epi, name='deletar_epi'),

    # --- ADVERTÊNCIAS ---
    path('advertencias/', dashboard_advertencias, name='dashboard_advertencias'),
    path('advertencias/config/', gerenciar_tipos_advertencia, name='config_advertencias'),
    path('advertencias/nova/', nova_advertencia, name='nova_advertencia'),
    path('advertencias/imprimir/<int:pk>/', imprimir_advertencia, name='imprimir_advertencia'),

    # --- EXTINTORES ---
    path('extintores/', dashboard_extintores, name='dashboard_extintores'),
    path('extintores/novo/', criar_editar_extintor, name='criar_extintor'),
    path('extintores/editar/<int:pk>/', criar_editar_extintor, name='editar_extintor'),
    path('extintores/inspecao/<int:extintor_id>/', registrar_inspecao, name='registrar_inspecao'),
    path('extintores/historico/<int:pk>/', historico_extintor, name='historico_extintor'),
    path('extintores/exportar/', exportar_extintores, name='exportar_extintores'),
    path('extintores/qrcode/<int:pk>/', gerar_qrcode, name='gerar_qrcode'),
    path('extintores/etiqueta/<int:pk>/', imprimir_etiqueta, name='imprimir_etiqueta'),
    path('extintores/scan/<int:pk>/', extintor_mobile, name='extintor_mobile'),

    # --- EQUIPAMENTOS ---
    path('equipamentos/', dashboard_equipamentos, name='dashboard_equipamentos'),
    path('equipamentos/novo/', criar_editar_equipamento, name='criar_equipamento'),
    path('equipamentos/editar/<int:pk>/', criar_editar_equipamento, name='editar_equipamento'),
    path('equipamentos/inspecao/<int:pk>/', inspecionar_equipamento, name='inspecionar_equipamento'),
    path('equipamentos/historico/<int:pk>/', historico_equipamento, name='historico_equipamento'),

    # --- PRODUTOS QUÍMICOS ---
    path('quimicos/', dashboard_quimicos, name='dashboard_quimicos'),
    path('quimicos/novo/', criar_editar_quimico, name='criar_quimico'),
    path('quimicos/editar/<int:pk>/', criar_editar_quimico, name='editar_quimico'),
    path('quimicos/deletar/<int:pk>/', deletar_quimico, name='deletar_quimico'),

    # --- HOSPITAIS E EMERGÊNCIAS (NOVOS) ---
    path('hospitais/', dashboard_hospitais, name='dashboard_hospitais'),
    path('hospitais/novo/', criar_editar_hospital, name='criar_hospital'),
    path('hospitais/editar/<int:pk>/', criar_editar_hospital, name='editar_hospital'),
    path('hospitais/config/', gerenciar_especialidades, name='gerenciar_especialidades'),
    
    # API (JSON)
    path('api/especialidades/nova/', api_criar_especialidade, name='api_criar_especialidade'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)