from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

from core.views import (
    # Views Originais
    cadastro_view, dashboard_view, criar_setor, 
    lista_funcionarios, criar_funcionario,
    lista_epis, criar_editar_epi, deletar_epi, 
    gerenciar_tipos, gerenciar_locais, gerenciar_vacinas,
    gerenciar_tipos_advertencia, nova_advertencia, 
    dashboard_advertencias, imprimir_advertencia,
    
    # Views de Extintores
    dashboard_extintores, criar_editar_extintor, 
    registrar_inspecao, historico_extintor, 
    exportar_extintores, gerar_qrcode, imprimir_etiqueta, extintor_mobile,

    # Views de Outros Equipamentos (Hidrantes, etc)
    dashboard_equipamentos, 
    criar_editar_equipamento, 
    inspecionar_equipamento,
    historico_equipamento,

    # --- NOVAS VIEWS: PRONTUÁRIO DO FUNCIONÁRIO ---
    detalhe_funcionario,
    adicionar_vacina_func,
    adicionar_epi_func,
    adicionar_treinamento_func
)

# Importe a nova view
from core.views import (
    # ...
    adicionar_advertencia_func
)


from core.views import (
    # ... outros imports ...
    editar_funcionario, # <--- IMPORTANTE: Adicione este nome na importação
)

from core.views import (
    # ... imports anteriores ...
    adicionar_afastamento_func,
    adicionar_acidente_func
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
    
    # --- FUNCIONÁRIOS E PRONTUÁRIO ---
    path('funcionarios/', lista_funcionarios, name='lista_funcionarios'),
    path('funcionarios/novo/', criar_funcionario, name='criar_funcionario'),
    # Novas rotas de detalhes e histórico
    path('funcionarios/<int:pk>/', detalhe_funcionario, name='detalhe_funcionario'),
    path('funcionarios/<int:func_id>/vacina/nova/', adicionar_vacina_func, name='adicionar_vacina_func'),
    path('funcionarios/<int:func_id>/epi/novo/', adicionar_epi_func, name='adicionar_epi_func'),
    path('funcionarios/<int:func_id>/treinamento/novo/', adicionar_treinamento_func, name='adicionar_treinamento_func'),

    # Configurações
    path('config/tipos-epi/', gerenciar_tipos, name='gerenciar_tipos'),
    path('config/locais/', gerenciar_locais, name='gerenciar_locais'),
    path('config/vacinas/', gerenciar_vacinas, name='gerenciar_vacinas'),

    # EPIs (Estoque)
    path('estoque/', lista_epis, name='lista_epis'),
    path('estoque/novo/', criar_editar_epi, name='criar_epi'),
    path('estoque/editar/<int:pk>/', criar_editar_epi, name='editar_epi'),
    path('estoque/deletar/<int:pk>/', deletar_epi, name='deletar_epi'),

    # Advertências
    path('advertencias/', dashboard_advertencias, name='dashboard_advertencias'),
    path('advertencias/config/', gerenciar_tipos_advertencia, name='config_advertencias'),
    path('advertencias/nova/', nova_advertencia, name='nova_advertencia'),
    path('advertencias/imprimir/<int:pk>/', imprimir_advertencia, name='imprimir_advertencia'),

    # Extintores
    path('extintores/', dashboard_extintores, name='dashboard_extintores'),
    path('extintores/novo/', criar_editar_extintor, name='criar_extintor'),
    path('extintores/editar/<int:pk>/', criar_editar_extintor, name='editar_extintor'),
    path('extintores/inspecao/<int:extintor_id>/', registrar_inspecao, name='registrar_inspecao'),
    path('extintores/historico/<int:pk>/', historico_extintor, name='historico_extintor'),
    path('extintores/exportar/', exportar_extintores, name='exportar_extintores'),
    path('extintores/qrcode/<int:pk>/', gerar_qrcode, name='gerar_qrcode'),
    path('extintores/etiqueta/<int:pk>/', imprimir_etiqueta, name='imprimir_etiqueta'),
    path('extintores/scan/<int:pk>/', extintor_mobile, name='extintor_mobile'),

    # Outros Equipamentos
    path('equipamentos/', dashboard_equipamentos, name='dashboard_equipamentos'),
    path('equipamentos/novo/', criar_editar_equipamento, name='criar_equipamento'),
    path('equipamentos/editar/<int:pk>/', criar_editar_equipamento, name='editar_equipamento'),
    path('equipamentos/inspecao/<int:pk>/', inspecionar_equipamento, name='inspecionar_equipamento'),
    path('equipamentos/historico/<int:pk>/', historico_equipamento, name='historico_equipamento'),
    path('funcionarios/<int:func_id>/advertencia/nova/', adicionar_advertencia_func, name='adicionar_advertencia_func'),

    path('funcionarios/editar/<int:pk>/', editar_funcionario, name='editar_funcionario'),
    
    path('funcionarios/<int:pk>/', detalhe_funcionario, name='detalhe_funcionario'),

    path('funcionarios/<int:func_id>/afastamento/novo/', adicionar_afastamento_func, name='adicionar_afastamento_func'),
    path('funcionarios/<int:func_id>/acidente/novo/', adicionar_acidente_func, name='adicionar_acidente_func'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)