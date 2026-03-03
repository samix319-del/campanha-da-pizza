import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Gestão Desbravadores",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Personalizado
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .stDataFrame { border-radius: 10px; }
    div[data-testid="stMetricValue"] { font-size: 24px; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# GERENCIAMENTO DE BANCO DE DADOS
# ==============================================================================
DB_NAME = "desbravadores.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campori (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_desbravador TEXT NOT NULL,
            nome_responsavel TEXT NOT NULL,
            p1 INTEGER DEFAULT 0,
            p2 INTEGER DEFAULT 0,
            p3 INTEGER DEFAULT 0,
            p4 INTEGER DEFAULT 0,
            valor_p1 REAL DEFAULT 97.00,
            valor_p2 REAL DEFAULT 97.00,
            valor_p3 REAL DEFAULT 97.00,
            valor_p4 REAL DEFAULT 97.00,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas_pizza (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_desbravador TEXT NOT NULL,
            quantidade INTEGER DEFAULT 0,
            valor_unitario REAL DEFAULT 0.0,
            data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_NAME)

def load_campori_data():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM campori ORDER BY id DESC", conn)
    conn.close()
    return df

def load_pizza_data():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM vendas_pizza ORDER BY quantidade DESC", conn)
    conn.close()
    return df

def update_campori_payment(id_registro, p1, p2, p3, p4, valor_p1, valor_p2, valor_p3, valor_p4):
    """Atualiza pagamentos de forma direta"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE campori 
        SET p1=?, p2=?, p3=?, p4=?, 
            valor_p1=?, valor_p2=?, valor_p3=?, valor_p4=?
        WHERE id=?
    ''', (p1, p2, p3, p4, valor_p1, valor_p2, valor_p3, valor_p4, id_registro))
    conn.commit()
    conn.close()

def save_pizza_df(df):
    conn = get_connection()
    cursor = conn.cursor()
    
    for index, row in df.iterrows():
        if pd.isna(row['id']) or row['id'] == 0:
            cursor.execute('''
                INSERT INTO vendas_pizza (nome_desbravador, quantidade, valor_unitario)
                VALUES (?, ?, ?)
            ''', (row['nome_desbravador'], int(row['quantidade']), float(row['valor_unitario'])))
        else:
            cursor.execute('''
                UPDATE vendas_pizza 
                SET nome_desbravador=?, quantidade=?, valor_unitario=?
                WHERE id=?
            ''', (row['nome_desbravador'], int(row['quantidade']), float(row['valor_unitario']), int(row['id'])))
    
    conn.commit()
    conn.close()
    st.success("✅ Dados de vendas atualizados!")

def delete_record(table, record_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()

# ==============================================================================
# INTERFACE DO USUÁRIO
# ==============================================================================

def main():
    init_db()
    
    st.sidebar.title("🔥 Clube de Desbravadores")
    st.sidebar.markdown("Sistema de Gestão Local")
    
    menu = st.sidebar.radio("Navegação", ["📊 Dashboard Geral", "🏕️ Controle Campori", "🍕 Ranking de Pizzas"])
    
    # --- DASHBOARD GERAL ---
    if menu == "📊 Dashboard Geral":
        st.title("📊 Visão Geral Financeira")
        
        df_campori = load_campori_data()
        df_pizza = load_pizza_data()
        
        total_parcelas_pagas = 0
        total_arrecadado_campori = 0.0
        
        if not df_campori.empty:
            for _, row in df_campori.iterrows():
                total_parcelas_pagas += row['p1'] + row['p2'] + row['p3'] + row['p4']
                total_arrecadado_campori += (row['p1'] * row['valor_p1'] if row['p1'] else 0)
                total_arrecadado_campori += (row['p2'] * row['valor_p2'] if row['p2'] else 0)
                total_arrecadado_campori += (row['p3'] * row['valor_p3'] if row['p3'] else 0)
                total_arrecadado_campori += (row['p4'] * row['valor_p4'] if row['p4'] else 0)
        
        total_arrecadado_pizza = 0.0
        if not df_pizza.empty:
            df_pizza['total_linha'] = df_pizza['quantidade'] * df_pizza['valor_unitario']
            total_arrecadado_pizza = df_pizza['total_linha'].sum()
            
        total_geral = total_arrecadado_campori + total_arrecadado_pizza
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Arrecadado Campori", f"R$ {total_arrecadado_campori:,.2f}", delta=f"{total_parcelas_pagas} parcelas pagas")
        col2.metric("Arrecadado Pizzas", f"R$ {total_arrecadado_pizza:,.2f}", delta="Vendas Ativas")
        col3.metric("TOTAL GERAL CAIXA", f"R$ {total_geral:,.2f}", delta="Saldo Atual")
        
        st.info("💡 Dica: Use o menu lateral para editar registros.")

    # --- ABA 1: CAMPORI ---
    elif menu == "🏕️ Controle Campori":
        st.title("🏕️ Controle de Pagamento - Campori")
        
        # Formulário de Novo Registro
        with st.expander("➕ Cadastrar Novo Desbravador"):
            with st.form("form_campori"):
                c1, c2 = st.columns(2)
                nome_desb = c1.text_input("Nome do Desbravador")
                nome_resp = c2.text_input("Nome do Responsável")
                submitted = st.form_submit_button("Salvar Registro")
                
                if submitted:
                    if nome_desb and nome_resp:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT INTO campori (nome_desbravador, nome_responsavel, 
                                valor_p1, valor_p2, valor_p3, valor_p4) 
                            VALUES (?, ?, 97.00, 97.00, 97.00, 97.00)
                        ''', (nome_desb, nome_resp))
                        conn.commit()
                        conn.close()
                        st.success("Cadastrado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Preencha todos os campos.")

        st.divider()
        
        df = load_campori_data()
        
        if not df.empty:
            st.subheader("📋 Registro de Pagamentos")
            
            # Criar colunas para cada registro
            for idx, row in df.iterrows():
                with st.expander(f"👤 {row['nome_desbravador']} - {row['nome_responsavel']} (ID: {row['id']})"):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    # Parcela 1
                    with col1:
                        st.markdown("**Parcela 1**")
                        p1 = st.checkbox("Paga", value=bool(row['p1']), key=f"p1_{row['id']}")
                        valor_p1 = st.number_input("Valor R$", min_value=0.0, value=float(row['valor_p1']), 
                                                   key=f"vp1_{row['id']}", step=1.0)
                    
                    # Parcela 2
                    with col2:
                        st.markdown("**Parcela 2**")
                        p2 = st.checkbox("Paga", value=bool(row['p2']), key=f"p2_{row['id']}")
                        valor_p2 = st.number_input("Valor R$", min_value=0.0, value=float(row['valor_p2']), 
                                                   key=f"vp2_{row['id']}", step=1.0)
                    
                    # Parcela 3
                    with col3:
                        st.markdown("**Parcela 3**")
                        p3 = st.checkbox("Paga", value=bool(row['p3']), key=f"p3_{row['id']}")
                        valor_p3 = st.number_input("Valor R$", min_value=0.0, value=float(row['valor_p3']), 
                                                   key=f"vp3_{row['id']}", step=1.0)
                    
                    # Parcela 4
                    with col4:
                        st.markdown("**Parcela 4**")
                        p4 = st.checkbox("Paga", value=bool(row['p4']), key=f"p4_{row['id']}")
                        valor_p4 = st.number_input("Valor R$", min_value=0.0, value=float(row['valor_p4']), 
                                                   key=f"vp4_{row['id']}", step=1.0)
                    
                    if st.button(f"💾 Salvar Pagamentos - {row['nome_desbravador']}", key=f"save_{row['id']}"):
                        update_campori_payment(row['id'], int(p1), int(p2), int(p3), int(p4),
                                             valor_p1, valor_p2, valor_p3, valor_p4)
                        st.success(f"✅ Pagamentos de {row['nome_desbravador']} salvos!")
                        st.rerun()
                    
                    # Calcular total pago
                    total_pago = 0
                    if p1: total_pago += valor_p1
                    if p2: total_pago += valor_p2
                    if p3: total_pago += valor_p3
                    if p4: total_pago += valor_p4
                    
                    st.info(f"💰 Total pago: R$ {total_pago:.2f} | Falta: R$ {(388.00 - total_pago):.2f}")
            
            # Área de Exclusão
            st.divider()
            st.subheader("🗑️ Excluir Registro")
            id_excluir = st.number_input("Digite o ID do registro para excluir", min_value=1, step=1)
            if st.button("Excluir Registro"):
                delete_record('campori', id_excluir)
                st.warning(f"Registro ID {id_excluir} excluído.")
                st.rerun()

            # Exportação
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar Relatório Campori (CSV)", csv, "relatorio_campori.csv", "text/csv")

        else:
            st.info("Nenhum registro encontrado. Cadastre acima.")

    # --- ABA 2: PIZZAS ---
    elif menu == "🍕 Ranking de Pizzas":
        st.title("🍕 Ranking de Vendas de Pizza")
        
        with st.expander("➕ Cadastrar Venda / Desbravador"):
            with st.form("form_pizza"):
                c1, c2, c3 = st.columns(3)
                nome_desb = c1.text_input("Nome do Desbravador")
                qtd = c2.number_input("Qtd. Pizzas Vendidas", min_value=0, step=1)
                valor = c3.number_input("Valor Unitário (R$)", min_value=0.0, step=0.50)
                submitted = st.form_submit_button("Registrar Venda")
                
                if submitted:
                    if nome_desb:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT INTO vendas_pizza (nome_desbravador, quantidade, valor_unitario) 
                            VALUES (?, ?, ?)
                        ''', (nome_desb, int(qtd), float(valor)))
                        conn.commit()
                        conn.close()
                        st.success("Venda registrada!")
                        st.rerun()
                    else:
                        st.error("Nome é obrigatório.")

        st.divider()
        
        df = load_pizza_data()
        
        if not df.empty:
            df['Total Arrecadado'] = df['quantidade'] * df['valor_unitario']
            df_ranking = df.sort_values(by='Total Arrecadado', ascending=False)
            
            st.subheader("📝 Editar Quantidades e Valores")
            
            edited_df = st.data_editor(
                df_ranking,
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "nome_desbravador": "Desbravador",
                    "quantidade": st.column_config.NumberColumn("Qtd Pizzas", min_value=0),
                    "valor_unitario": st.column_config.NumberColumn("Valor Unit. (R$)", min_value=0.0),
                    "Total Arrecadado": st.column_config.NumberColumn("Total (R$)", disabled=True),
                },
                hide_index=True,
                use_container_width=True
            )
            
            if st.button("💾 Atualizar Vendas"):
                save_pizza_df(edited_df)
                st.rerun()
            
            st.divider()
            st.subheader("🗑️ Excluir Registro")
            id_excluir_pizza = st.number_input("ID para excluir venda", min_value=1, step=1, key="pizza_del")
            if st.button("Excluir Venda"):
                delete_record('vendas_pizza', id_excluir_pizza)
                st.rerun()
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar Ranking Pizzas (CSV)", csv, "ranking_pizzas.csv", "text/csv")

        else:
            st.info("Nenhuma venda registrada ainda.")

if __name__ == "__main__":
    main()
