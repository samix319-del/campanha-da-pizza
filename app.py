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

# CSS Personalizado para cores e layout
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .stDataFrame { border-radius: 10px; }
    div[data-testid="stMetricValue"] { font-size: 24px; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# GERENCIAMENTO DE BANCO DE DADOS (SQLite)
# ==============================================================================
DB_NAME = "desbravadores.db"

def init_db():
    """Cria as tabelas se não existirem."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabela Campori
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campori (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_desbravador TEXT NOT NULL,
            nome_responsavel TEXT NOT NULL,
            p1 INTEGER DEFAULT 0,
            p2 INTEGER DEFAULT 0,
            p3 INTEGER DEFAULT 0,
            p4 INTEGER DEFAULT 0,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela Vendas Pizza
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

def save_campori_df(df):
    """Sincroniza o DataFrame editado de volta para o SQLite."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Iterar sobre as linhas para atualizar
    for index, row in df.iterrows():
        # Verifica se é uma nova linha (ID NaN ou 0) ou atualização
        if pd.isna(row['id']) or row['id'] == 0:
            cursor.execute('''
                INSERT INTO campori (nome_desbravador, nome_responsavel, p1, p2, p3, p4)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (row['nome_desbravador'], row['nome_responsavel'], 
                  int(row['p1']), int(row['p2']), int(row['p3']), int(row['p4'])))
        else:
            cursor.execute('''
                UPDATE campori 
                SET nome_desbravador=?, nome_responsavel=?, p1=?, p2=?, p3=?, p4=?
                WHERE id=?
            ''', (row['nome_desbravador'], row['nome_responsavel'],
                  int(row['p1']), int(row['p2']), int(row['p3']), int(row['p4']),
                  int(row['id'])))
    
    conn.commit()
    conn.close()
    st.success("Dados de Campori salvos com sucesso!")

def save_pizza_df(df):
    """Sincroniza o DataFrame editado de volta para o SQLite."""
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
    st.success("Dados de Vendas atualizados!")

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
    init_db() # Garante que o DB existe ao iniciar
    
    st.sidebar.title("🔥 Clube de Desbravadores")
    st.sidebar.markdown("Sistema de Gestão Local")
    
    menu = st.sidebar.radio("Navegação", ["📊 Dashboard Geral", "🏕️ Controle Campori", "🍕 Ranking de Pizzas"])
    
    # --- DASHBOARD GERAL ---
    if menu == "📊 Dashboard Geral":
        st.title("📊 Visão Geral Financeira")
        
        df_campori = load_campori_data()
        df_pizza = load_pizza_data()
        
        # Cálculos Campori
        total_parcelas_pagas = 0
        if not df_campori.empty:
            cols_pagas = ['p1', 'p2', 'p3', 'p4']
            total_parcelas_pagas = df_campori[cols_pagas].sum().sum()
        
        valor_campori = total_parcelas_pagas * 97.00
        
        # Cálculos Pizza
        total_arrecadado_pizza = 0.0
        if not df_pizza.empty:
            df_pizza['total_linha'] = df_pizza['quantidade'] * df_pizza['valor_unitario']
            total_arrecadado_pizza = df_pizza['total_linha'].sum()
            
        total_geral = valor_campori + total_arrecadado_pizza
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Arrecadado Campori", f"R$ {valor_campori:,.2f}", delta=f"{total_parcelas_pagas} parcelas pagas")
        col2.metric("Arrecadado Pizzas", f"R$ {total_arrecadado_pizza:,.2f}", delta="Vendas Ativas")
        col3.metric("TOTAL GERAL CAIXA", f"R$ {total_geral:,.2f}", delta="Saldo Atual")
        
        st.info("💡 Dica: Use o menu lateral para editar registros ou lançar novos pagamentos/vendas.")

    # --- ABA 1: CAMPORI ---
    elif menu == "🏕️ Controle Campori":
        st.title("🏕️ Controle de Pagamento - Campori")
        st.markdown("**Valor da Parcela:** R$ 97,00 | **Total por Desbravador:** R$ 388,00")
        
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
                        cursor.execute("INSERT INTO campori (nome_desbravador, nome_responsavel) VALUES (?, ?)", (nome_desb, nome_resp))
                        conn.commit()
                        conn.close()
                        st.success("Cadastrado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Preencha todos os campos.")

        st.divider()
        
        # Carregar e Exibir Dados
        df = load_campori_data()
        
        if not df.empty:
            # Preparar DataFrame para Edição
            # Renomear colunas para exibição amigável
            df_edit = df.copy()
            df_edit = df_edit.rename(columns={
                'p1': 'Parcela 1 (R$97)', 
                'p2': 'Parcela 2 (R$97)', 
                'p3': 'Parcela 3 (R$97)', 
                'p4': 'Parcela 4 (R$97)'
            })
            
            # Configurar o editor de dados
            edited_df = st.data_editor(
                df_edit,
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "nome_desbravador": st.column_config.TextColumn("Desbravador"),
                    "nome_responsavel": st.column_config.TextColumn("Responsável"),
                    "Parcela 1 (R$97)": st.column_config.CheckboxColumn("P1", help="Marcar como pago"),
                    "Parcela 2 (R$97)": st.column_config.CheckboxColumn("P2", help="Marcar como pago"),
                    "Parcela 3 (R$97)": st.column_config.CheckboxColumn("P3", help="Marcar como pago"),
                    "Parcela 4 (R$97)": st.column_config.CheckboxColumn("P4", help="Marcar como pago"),
                },
                hide_index=True,
                use_container_width=True,
                num_rows="dynamic" # Permite adicionar linhas direto na tabela se quiser
            )
            
            # Botão de Salvar Alterações da Tabela
            if st.button("💾 Salvar Alterações dos Pagamentos"):
                save_campori_df(edited_df)
                st.rerun()
                
            # Área de Exclusão
            st.divider()
            st.subheader("🗑️ Excluir Registro")
            id_excluir = st.number_input("Digite o ID do registro para excluir permanentemente", min_value=1, step=1)
            if st.button("Excluir Registro"):
                delete_record('campori', id_excluir)
                st.warning(f"Registro ID {id_excluir} excluído.")
                st.rerun()

            # Cálculo de Saldo por Desbravador (Visualização apenas)
            st.divider()
            st.subheader("💰 Status de Saldo")
            df_calc = df.copy()
            df_calc['total_pago'] = (df_calc['p1'] + df_calc['p2'] + df_calc['p3'] + df_calc['p4']) * 97.00
            df_calc['faltam'] = 388.00 - df_calc['total_pago']
            
            display_df = df_calc[['nome_desbravador', 'total_pago', 'faltam']]
            display_df = display_df.rename(columns={'total_pago': 'Já Pago', 'faltam': 'Falta Pagar'})
            
            # Formatar moeda para exibição
            st.dataframe(
                display_df.style.format({'Já Pago': 'R$ {:,.2f}', 'Falta Pagar': 'R$ {:,.2f}'}),
                use_container_width=True,
                hide_index=True
            )
            
            # Exportação
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar Relatório Campori (CSV)", csv, "relatorio_campori.csv", "text/csv")

        else:
            st.info("Nenhum registro encontrado. Cadastre acima.")

    # --- ABA 2: PIZZAS ---
    elif menu == "🍕 Ranking de Pizzas":
        st.title("🍕 Ranking de Vendas de Pizza")
        
        # Formulário de Nova Venda/Desbravador
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
                        cursor.execute("INSERT INTO vendas_pizza (nome_desbravador, quantidade, valor_unitario) VALUES (?, ?, ?)", 
                                       (nome_desb, int(qtd), float(valor)))
                        conn.commit()
                        conn.close()
                        st.success("Venda registrada!")
                        st.rerun()
                    else:
                        st.error("Nome é obrigatório.")

        st.divider()
        
        df = load_pizza_data()
        
        if not df.empty:
            # Cálculo Automático do Total
            df['Total Arrecadado'] = df['quantidade'] * df['valor_unitario']
            
            # Ordenar para o Ranking (Maior para Menor)
            df_ranking = df.sort_values(by='Total Arrecadado', ascending=False)
            
            # Exibir Tabela Editável
            st.subheader("📝 Editar Quantidades e Valores")
            st.caption("Edite diretamente na tabela abaixo para atualizar vendas.")
            
            edited_df = st.data_editor(
                df_ranking,
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "nome_desbravador": "Desbravador",
                    "quantidade": st.column_config.NumberColumn("Qtd Pizzas", min_value=0),
                    "valor_unitario": st.column_config.NumberColumn("Valor Unit. (R$)", min_value=0.0),
                    "Total Arrecadado": st.column_config.NumberColumn("Total (R$)", disabled=True), # Calculado automaticamente pelo pandas antes, mas aqui é estático na edição
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Recalcular totais do DF editado para salvar corretamente
            # Nota: O data_editor não recalcula colunas derivadas automaticamente no backend
            # Precisamos garantir que o save use os dados brutos
            
            if st.button("💾 Atualizar Vendas"):
                # Antes de salvar, garantimos que a lógica de total seja consistente se necessário
                # Mas como salvamos qtd e valor, o total é derivado.
                save_pizza_df(edited_df)
                st.rerun()

            # Área de Exclusão
            st.divider()
            st.subheader("🗑️ Excluir Registro")
            id_excluir_pizza = st.number_input("ID para excluir venda", min_value=1, step=1, key="pizza_del")
            if st.button("Excluir Venda"):
                delete_record('vendas_pizza', id_excluir_pizza)
                st.rerun()
            
            # Exportação
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar Ranking Pizzas (CSV)", csv, "ranking_pizzas.csv", "text/csv")

        else:
            st.info("Nenhuma venda registrada ainda.")

if __name__ == "__main__":
    main()