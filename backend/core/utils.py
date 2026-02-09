from .models import InventarioRisco

def obrigacoes_funcionario(funcionario):
    inventarios = InventarioRisco.objects.filter(
        empresa=funcionario.empresa,
        setor=funcionario.setor,
        funcao=funcionario.funcao
    )

    epis = set()
    treinamentos = set()
    exames = set()

    for inv in inventarios:
        epis.update(inv.epis_obrigatorios.all())
        treinamentos.update(inv.treinamentos_obrigatorios.all())
        exames.update(inv.exames_obrigatorios.all())

    return {
        "epis": epis,
        "treinamentos": treinamentos,
        "exames": exames,
    }
