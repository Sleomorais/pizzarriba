from fastapi import APIRouter, Depends, HTTPException

from dependecies import pegar_sessao, verificar_token
from schemas import ItemPedidoSchema, PedidoSchema, ResponsePedidoSchema
from sqlalchemy.orm import Session
from models import ItemPedido, Pedidos, Usuario
from typing import List

order_router = APIRouter(prefix="/pedidos", tags=["pedidos"], dependencies=[Depends(verificar_token)])

@order_router.get("/")
async def ver_pedidos():
    """
    Essa é a rota para ver os todos os pedidos
    """
    return [{"id": 1}, {"id": 2}]



@order_router.post("/pedido")
async def criar_pedido(pedido_schema: PedidoSchema, session: Session = Depends(pegar_sessao)):
    novo_pedido = Pedidos(usuario=pedido_schema.usuario)
    session.add(novo_pedido)
    session.commit()
    return {"mensagem": f"Pedido criado com sucesso. ID do pedido: {novo_pedido.id}"}


@order_router.post("pedido/cancelar/{id_pedido}")
async def cancelar_pedido(id_pedido: int, session: Session = Depends(pegar_sessao), usuario: Usuario = Depends(verificar_token)):
    pedido = session.query(Pedidos).filter(Pedidos.id == id_pedido).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")
    
    if not usuario.admin and pedido.usuario != usuario.id:
        raise HTTPException(status_code=401, detail="Nao autorizado")
    pedido.status = "CANCELADO"
    session.commit()
    return {
        "mensagem": f"Pedido {pedido.id} cancelado com sucesso", 
        "pedido": pedido
    }


@order_router.get("/listar")
async def listar_pedidos(session: Session = Depends(pegar_sessao), usuario: Usuario = Depends(verificar_token)):
    if not usuario.admin: 
        raise HTTPException(status_code=401, detail="Nao autorizado")
    else:
        pedidos = session.query(Pedidos).all()
        return {"pedidos": pedidos}
    

@order_router.post("/pedido/adicionar-item/{id_pedido}")
async def adicionar_item_pedido(id_pedido: int, item_pedido_schema: ItemPedidoSchema, session: Session = Depends(pegar_sessao), usuario: Usuario = Depends(verificar_token)):
    pedido = session.query(Pedidos).filter(Pedidos.id == id_pedido).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")
    if not usuario.admin and pedido.usuario != usuario.id:
        raise HTTPException(status_code=401, detail="Nao autorizado")

    novo_item_pedido = ItemPedido(quantidade=item_pedido_schema.quantidade, sabor=item_pedido_schema.sabor, tamanho=item_pedido_schema.tamanho, 
                                  preco_unitario=item_pedido_schema.preco_unitario, pedido=id_pedido)
    pedido.itens.add(novo_item_pedido)
    Pedidos.calcular_preco()
    session.commit()
    return {"mensagem": f"Item adicionado ao pedido com sucesso", 
            "id_item_pedido": novo_item_pedido.id,
            "pedido": pedido}



@order_router.post("/pedido/remover-item/{id_item_pedido}")
async def remover_item_pedido(id_item_pedido: int, session: Session = Depends(pegar_sessao), usuario: Usuario = Depends(verificar_token)):
    item_pedido = session.query(ItemPedido).filter(ItemPedido.id == id_item_pedido).first()
    pedido = session.query(Pedidos).filter(Pedidos.id == item_pedido.pedido).first()
    if not item_pedido:
        raise HTTPException(status_code=404, detail="Item do pedido nao encontrado")
    if not usuario.admin and pedido.usuario != usuario.id:
        raise HTTPException(status_code=401, detail="Nao autorizado")

    
    session.delete(item_pedido)
    pedido.calcular_preco()
    session.commit()
    return {
        "mensagem": f"Item removido do pedido com sucesso", 
        "pedido_itens": pedido.itens,
    }


@order_router.post("pedido/finalizar/{id_pedido}")
async def finalizar_pedido(id_pedido: int, session: Session = Depends(pegar_sessao), usuario: Usuario = Depends(verificar_token)):
    pedido = session.query(Pedidos).filter(Pedidos.id == id_pedido).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")
    
    if not usuario.admin and pedido.usuario != usuario.id:
        raise HTTPException(status_code=401, detail="Nao autorizado")
    pedido.status = "FINALIZADO"
    session.commit()
    return {
        "mensagem": f"Pedido {pedido.id} finalizado com sucesso", 
        "pedido": pedido
    }

@order_router.get("/pedido/{id_pedido}", response_model= ResponsePedidoSchema)
async def visualizar_pedido(id_pedido: int, session: Session = Depends(pegar_sessao), usuario: Usuario = Depends(verificar_token)):
    pedido = session.query(Pedidos).filter(Pedidos.id == id_pedido).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")
    if not usuario.admin and pedido.usuario != usuario.id:
        raise HTTPException(status_code=401, detail="Nao autorizado")
    return {
        "quantidade_itens": len(pedido.itens),
        "pedido": pedido
    }


@order_router.get("/listar/pedidos-usuario", response_model= List[ResponsePedidoSchema])
async def listar_pedidos(session: Session = Depends(pegar_sessao), usuario: Usuario = Depends(verificar_token)):
    pedidos = session.query(Pedidos).filter(Pedidos.usuario == usuario.id).all()
    return pedidos


