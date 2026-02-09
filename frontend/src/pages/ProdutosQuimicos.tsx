import { useEffect, useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Progress } from "@/components/ui/progress";
import {
  Search,
  Plus,
  AlertTriangle,
  Skull,
  Flame,
  Droplets,
  Wind,
  Download,
  Eye,
  MapPin,
  Users,
  TriangleAlert,
  MoreVertical,
  Pencil,
  Trash2,
  Box,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2
} from "lucide-react";
import { toast } from "sonner";

// --- TIPAGEM ---
interface ProdutoAPI {
  id: number;
  nome: string;
  cas_number: string;
  concentracao: string;
  quantidade: number;
  unidade: string;
  localizacao: { id: number; nome: string } | null;
  data_validade: string;
  status_validade: string;
  fispq: string | null;
  ghs_riscos: string[];
}

interface ProdutoUI {
  id: number;
  nome: string;
  cas: string;
  concentracao: string;
  classificacaoGHS: string[];
  setor: string;
  localizacao: string;
  quantidade: number;
  unidade: string;
  fispqValidade: string;
  fispqStatus: string;
  fispqUrl: string | null;
  hasFispq: boolean;
}

// --- COMPONENTES AUXILIARES ---
const GHSDiamond = ({ tipo }: { tipo: string }) => {
  let Icon = AlertTriangle;
  
  // Normaliza o texto para pegar o ícone certo (remove acentos e minúsculas para comparar)
  const tipoNorm = tipo.toLowerCase();

  if (tipoNorm.includes("corrosivo")) Icon = Droplets;
  else if (tipoNorm.includes("inflam") || tipoNorm.includes("fogo")) Icon = Flame;
  else if (tipoNorm.includes("toxico") || tipoNorm.includes("tóxico")) Icon = Skull;
  else if (tipoNorm.includes("irritante")) Icon = AlertCircle;
  else if (tipoNorm.includes("oxidante")) Icon = Wind;

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="relative group cursor-help mx-1 my-1">
            <div className="w-8 h-8 border-[2px] border-red-600 bg-white rotate-45 rounded-sm shadow-sm flex items-center justify-center transition-transform group-hover:scale-110">
              <div className="-rotate-45">
                <Icon className="w-4 h-4 text-black fill-current" />
              </div>
            </div>
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <p className="font-semibold capitalize">{tipo}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

const getFispqStatus = (status: string, date: string) => {
  const dateFormatted = date ? new Date(date).toLocaleDateString("pt-BR") : "-";
  
  // Mapeia o status que vem do Python ('vencido', 'alerta', 'ok')
  if (status === "ok" || status === "valida") {
    return (
      <div className="flex flex-col items-start">
        <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 mb-1 gap-1">
          <CheckCircle2 className="w-3 h-3" /> Válida
        </Badge>
        <span className="text-[10px] text-muted-foreground ml-1">Vence: {dateFormatted}</span>
      </div>
    );
  } else if (status === "vencido" || status === "vencida") {
    return (
      <div className="flex flex-col items-start">
        <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200 mb-1 gap-1">
          <XCircle className="w-3 h-3" /> Vencida
        </Badge>
        <span className="text-[10px] text-muted-foreground ml-1">Venceu: {dateFormatted}</span>
      </div>
    );
  } else {
    return (
      <div className="flex flex-col items-start">
        <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200 mb-1 gap-1">
          <AlertTriangle className="w-3 h-3" /> Renovar
        </Badge>
        <span className="text-[10px] text-muted-foreground ml-1">Vence: {dateFormatted}</span>
      </div>
    );
  }
};

export default function ProdutosQuimicos() {
  const [produtos, setProdutos] = useState<ProdutoUI[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterSetor, setFilterSetor] = useState("todos");
  const [isModalOpen, setIsModalOpen] = useState(false);

  // --- FETCH DATA DO DJANGO ---
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Tenta buscar da API local (Django)
        const response = await fetch("http://127.0.0.1:8000/api/quimicos/");
        
        if (!response.ok) {
          throw new Error("Erro ao conectar com servidor");
        }

        const data: ProdutoAPI[] = await response.json();

        // Converte os dados do Python para o formato da Interface UI
        const produtosFormatados: ProdutoUI[] = data.map((item) => ({
          id: item.id,
          nome: item.nome,
          cas: item.cas_number || "-",
          concentracao: item.concentracao || "-",
          classificacaoGHS: item.ghs_riscos && item.ghs_riscos.length > 0 ? item.ghs_riscos : ["Geral"],
          setor: item.localizacao?.nome || "Geral", // Assume que a localização define o setor
          localizacao: item.localizacao?.nome || "Não definido",
          quantidade: item.quantidade,
          unidade: item.unidade,
          fispqValidade: item.data_validade,
          fispqStatus: item.status_validade,
          fispqUrl: item.fispq,
          hasFispq: !!item.fispq,
        }));

        setProdutos(produtosFormatados);
      } catch (error) {
        console.error("Erro ao buscar produtos:", error);
        toast.error("Não foi possível carregar os dados. Verifique se o backend está rodando.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const filteredProdutos = produtos.filter((produto) => {
    const matchesSearch =
      produto.nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
      produto.cas.includes(searchTerm);
    const matchesSetor = filterSetor === "todos" || produto.setor === filterSetor;
    return matchesSearch && matchesSetor;
  });

  return (
    <div className="space-y-6 font-sans p-6">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Produtos Químicos</h1>
          <p className="text-slate-500 mt-1">
            Gestão de FISPQ, inventário e riscos GHS (Integrado ao Django)
          </p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} className="bg-blue-600 hover:bg-blue-700 shadow-sm gap-2">
          <Plus className="w-4 h-4" /> Novo Produto
        </Button>
      </div>

      <Tabs defaultValue="inventario" className="space-y-6">
        <TabsList className="bg-slate-100/50 p-1 border rounded-full inline-flex h-auto gap-2">
          <TabsTrigger value="inventario" className="rounded-full px-4 py-2 data-[state=active]:bg-white data-[state=active]:text-blue-700 data-[state=active]:shadow-sm">
            <Box className="w-4 h-4 mr-2" /> Inventário
          </TabsTrigger>
          <TabsTrigger value="riscos" className="rounded-full px-4 py-2 data-[state=active]:bg-white data-[state=active]:text-blue-700 data-[state=active]:shadow-sm">
            <MapPin className="w-4 h-4 mr-2" /> Mapa de Riscos
          </TabsTrigger>
        </TabsList>

        <TabsContent value="inventario">
          <Card className="border-0 shadow-sm ring-1 ring-slate-200">
            <CardHeader className="border-b bg-slate-50/50 py-4">
              <div className="flex flex-col sm:flex-row gap-4 justify-between items-center">
                <div className="relative w-full max-w-md">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
                  <Input
                    placeholder="Buscar por nome, CAS ou código..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 bg-white border-slate-200"
                  />
                </div>
                <Select value={filterSetor} onValueChange={setFilterSetor}>
                  <SelectTrigger className="w-[200px] bg-white border-slate-200">
                    <SelectValue placeholder="Filtrar por Setor" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="todos">Todos os Setores</SelectItem>
                    {/* Extrai setores únicos da lista de produtos */}
                    {Array.from(new Set(produtos.map(p => p.setor))).map(setor => (
                       <SelectItem key={setor} value={setor}>{setor}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader className="bg-slate-50">
                  <TableRow>
                    <TableHead className="pl-6 py-3 font-semibold text-slate-600 uppercase text-xs">Produto</TableHead>
                    <TableHead className="font-semibold text-slate-600 uppercase text-xs">CAS / Ref</TableHead>
                    <TableHead className="font-semibold text-slate-600 uppercase text-xs">Classificação GHS</TableHead>
                    <TableHead className="font-semibold text-slate-600 uppercase text-xs">Setor / Local</TableHead>
                    <TableHead className="font-semibold text-slate-600 uppercase text-xs">Estoque</TableHead>
                    <TableHead className="font-semibold text-slate-600 uppercase text-xs">FISPQ</TableHead>
                    <TableHead className="pr-6 text-right font-semibold text-slate-600 uppercase text-xs">Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading ? (
                    <TableRow>
                      <TableCell colSpan={7} className="h-32 text-center">
                        <div className="flex flex-col items-center justify-center text-slate-500 gap-2">
                          <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
                          Carregando dados do servidor...
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : filteredProdutos.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="h-32 text-center text-slate-500">
                        Nenhum produto encontrado ou cadastrado.
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredProdutos.map((produto) => (
                      <TableRow key={produto.id} className="hover:bg-slate-50/50 transition-colors">
                        <TableCell className="pl-6">
                          <div className="flex flex-col">
                            <span className="font-semibold text-slate-900">{produto.nome}</span>
                            <span className="text-xs text-slate-500">{produto.concentracao}</span>
                          </div>
                        </TableCell>
                        
                        <TableCell>
                          <Badge variant="secondary" className="font-mono text-xs text-slate-600 bg-slate-100 border-slate-200">
                            {produto.cas}
                          </Badge>
                        </TableCell>

                        <TableCell>
                          <div className="flex items-center flex-wrap gap-1">
                            {produto.classificacaoGHS.map((ghs, idx) => (
                              <GHSDiamond key={`${produto.id}-${idx}`} tipo={ghs} />
                            ))}
                          </div>
                        </TableCell>

                        <TableCell>
                          <div className="flex flex-col">
                            <span className="text-sm font-medium text-slate-700">{produto.setor}</span>
                            <span className="text-xs text-slate-500 flex items-center gap-1">
                              <MapPin className="w-3 h-3" /> {produto.localizacao}
                            </span>
                          </div>
                        </TableCell>

                        <TableCell>
                          <Badge variant="outline" className="font-medium bg-white text-slate-700 border-slate-300">
                            {produto.quantidade} {produto.unidade}
                          </Badge>
                        </TableCell>

                        <TableCell>
                          {getFispqStatus(produto.fispqStatus, produto.fispqValidade)}
                        </TableCell>

                        <TableCell className="pr-6 text-right">
                          <div className="flex justify-end items-center gap-1">
                            {produto.hasFispq && produto.fispqUrl && (
                              <>
                                <TooltipProvider>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <a href={`http://127.0.0.1:8000${produto.fispqUrl}`} target="_blank" rel="noreferrer">
                                        <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-500 hover:text-blue-600 hover:bg-blue-50">
                                          <Eye className="w-4 h-4" />
                                        </Button>
                                      </a>
                                    </TooltipTrigger>
                                    <TooltipContent>Visualizar</TooltipContent>
                                  </Tooltip>
                                </TooltipProvider>

                                <TooltipProvider>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <a href={`http://127.0.0.1:8000${produto.fispqUrl}`} download>
                                        <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-500 hover:text-blue-600 hover:bg-blue-50">
                                          <Download className="w-4 h-4" />
                                        </Button>
                                      </a>
                                    </TooltipTrigger>
                                    <TooltipContent>Baixar</TooltipContent>
                                  </Tooltip>
                                </TooltipProvider>
                              </>
                            )}
                            
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-400 hover:text-slate-700">
                                  <MoreVertical className="w-4 h-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuLabel>Opções</DropdownMenuLabel>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem>
                                  <Pencil className="w-4 h-4 mr-2" /> Editar
                                </DropdownMenuItem>
                                <DropdownMenuItem className="text-red-600">
                                  <Trash2 className="w-4 h-4 mr-2" /> Excluir
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
        
        {/* Placeholder para outras tabs */}
        <TabsContent value="riscos">
           <div className="p-4 text-center text-slate-500">Funcionalidade em desenvolvimento...</div>
        </TabsContent>
      </Tabs>

      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent>
          <DialogHeader>
             <DialogTitle>Novo Produto</DialogTitle>
             <DialogDescription>Para adicionar, use o painel Administrativo por enquanto.</DialogDescription>
          </DialogHeader>
        </DialogContent>
      </Dialog>
    </div>
  );
}