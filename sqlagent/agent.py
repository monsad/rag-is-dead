import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities.sql_database import SQLDatabase
from langchain.tools.retriever import create_retriever_tool
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from sklearn.linear_model import LinearRegression # Prosty model predykcyjny

# --- 1. Loading Environment Variables ---
load_dotenv()

# Database Configuration
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Creating URI for Langchain SQLDatabase
DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# --- 2. Database Connection (Helper Function) ---
def get_db_connection():
    """Database connection"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Connection error: {e}")
        return None

def attempt_to_fix_sql(failed_query: str, error_message: str, db_schema: str) -> str:
    """Attempts to fix a failed SQL query based on the error message and database schema."""
    # This is a simplified example. In a real-world scenario, you might use a more
    # sophisticated approach, potentially involving another LLM call with specific instructions.
    print("\n--- 🔧 Attempting to fix SQL query ---")
    prompt = f"""The following SQL query failed:\n\n`{failed_query}`\n\nWith this error:\n\n`{error_message}`\n\nHere is the relevant database schema:\n\n`{db_schema}`\n\nPlease try to fix the query. Only return the corrected SQL query, with no other text."""

    try:
        response = llm.invoke(prompt)
        # Assuming the LLM returns just the fixed SQL query.
        # In a real application, you'd want to parse this more carefully.
        fixed_sql = response.content.strip().replace('`', '')
        print(f"💡 Suggested fix: {fixed_sql}")
        return fixed_sql
    except Exception as e:
        print(f"❌ Could not get a fix from the LLM: {e}")
        return None

# --- 3. Advanced Prediction Module ---
class BusinessRevenuePredictionModel:
    """Advanced revenue prediction model based on real business data."""
    def __init__(self):
        self.mrc_model = LinearRegression()  # Model for Monthly Recurring Revenue (MRC)
        self.nrc_model = LinearRegression()  # Model for Non-Recurring Revenue (NRC)
        self.is_trained = False
        self.last_training_date = None
        self.training_stats = {}

    def fetch_business_data(self, conn):
        """Fetches real business data from the database."""
        cursor = conn.cursor()
        
        # Query joining data from quotes and accounts for comprehensive analysis
        query = """
        WITH monthly_revenue AS (
            SELECT 
                DATE_TRUNC('month', q.created_at) as month,
                SUM(COALESCE(q.total_mrc_contracted_currency, 0)) as total_mrc,
                SUM(COALESCE(q.total_nrc_contracted_currency, 0)) as total_nrc,
                COUNT(q.uuid) as deal_count,
                COUNT(CASE WHEN q.status = 'closed_won' THEN 1 END) as won_deals,
                COUNT(CASE WHEN a.account_type = 'Customer' THEN 1 END) as customer_deals,
                COUNT(CASE WHEN a.account_type = 'Supplier' THEN 1 END) as supplier_deals,
                AVG(CASE WHEN q.close_date IS NOT NULL THEN 
                    EXTRACT(DAYS FROM (q.close_date - q.created_at)) END) as avg_deal_duration
            FROM quotes_quotecontainer q
            LEFT JOIN accounts_account a ON q.account_id = a.id
            WHERE q.created_at >= NOW() - INTERVAL '24 months'
            AND q.deleted IS NULL
            GROUP BY DATE_TRUNC('month', q.created_at)
            ORDER BY month
        ),
        product_revenue AS (
            SELECT 
                DATE_TRUNC('month', p.start_date) as month,
                SUM(COALESCE(p.mrc, 0)) as product_mrc,
                SUM(COALESCE(p.nrc, 0)) as product_nrc,
                COUNT(p.id) as active_products
            FROM products_productv2 p
            WHERE p.start_date >= NOW() - INTERVAL '24 months'
            AND p.deleted IS NULL
            AND p.status = 'active'
            GROUP BY DATE_TRUNC('month', p.start_date)
            ORDER BY month
        )
        SELECT 
            COALESCE(mr.month, pr.month) as month,
            COALESCE(mr.total_mrc, 0) + COALESCE(pr.product_mrc, 0) as total_mrc,
            COALESCE(mr.total_nrc, 0) + COALESCE(pr.product_nrc, 0) as total_nrc,
            COALESCE(mr.deal_count, 0) as deal_count,
            COALESCE(mr.won_deals, 0) as won_deals,
            COALESCE(mr.customer_deals, 0) as customer_deals,
            COALESCE(mr.supplier_deals, 0) as supplier_deals,
            COALESCE(mr.avg_deal_duration, 0) as avg_deal_duration,
            COALESCE(pr.active_products, 0) as active_products
        FROM monthly_revenue mr
        FULL OUTER JOIN product_revenue pr ON mr.month = pr.month
        ORDER BY COALESCE(mr.month, pr.month);
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        if not results:
            return None
            
        columns = ['month', 'total_mrc', 'total_nrc', 'deal_count', 'won_deals', 
                  'customer_deals', 'supplier_deals', 'avg_deal_duration', 'active_products']
        
        return pd.DataFrame(results, columns=columns)

    def create_features(self, data: pd.DataFrame):
        """Creates advanced features for the prediction model."""
        data = data.copy()
        data['month'] = pd.to_datetime(data['month'])
        data = data.sort_values('month').reset_index(drop=True)
        
        # Basic time features
        data['month_ordinal'] = data['month'].apply(lambda x: x.toordinal())
        data['year'] = data['month'].dt.year
        data['month_num'] = data['month'].dt.month
        data['quarter'] = data['month'].dt.quarter
        
        # Seasonal features
        data['is_q4'] = (data['quarter'] == 4).astype(int)  # Q4 often has higher sales
        data['is_q1'] = (data['quarter'] == 1).astype(int)  # Q1 may have slower start
        
        # Business indicators
        data['win_rate'] = data['won_deals'] / (data['deal_count'] + 1e-6)  # Avoid division by zero
        data['customer_supplier_ratio'] = data['customer_deals'] / (data['supplier_deals'] + 1e-6)
        
        # Trends (moving averages)
        data['mrc_ma3'] = data['total_mrc'].rolling(window=3, min_periods=1).mean()
        data['nrc_ma3'] = data['total_nrc'].rolling(window=3, min_periods=1).mean()
        data['mrc_ma6'] = data['total_mrc'].rolling(window=6, min_periods=1).mean()
        
        # Month-to-month growth
        data['mrc_growth'] = data['total_mrc'].pct_change().fillna(0)
        data['nrc_growth'] = data['total_nrc'].pct_change().fillna(0)
        
        # Lagged features
        data['mrc_lag1'] = data['total_mrc'].shift(1).fillna(data['total_mrc'].mean())
        data['nrc_lag1'] = data['total_nrc'].shift(1).fillna(data['total_nrc'].mean())
        
        return data

    def train(self, data: pd.DataFrame):
        """Trains advanced revenue prediction models."""
        if data is None or data.empty:
            print("No business data available to train the prediction model.")
            self.is_trained = False
            return

        try:
            # Prepare features
            featured_data = self.create_features(data)
            
            # Save training statistics
            self.training_stats = {
                'data_points': len(featured_data),
                'date_range': f"{featured_data['month'].min()} to {featured_data['month'].max()}",
                'avg_mrc': featured_data['total_mrc'].mean(),
                'avg_nrc': featured_data['total_nrc'].mean(),
                'total_mrc': featured_data['total_mrc'].sum(),
                'total_nrc': featured_data['total_nrc'].sum()
            }
            
            self.last_training_date = featured_data['month'].max()
            
            # Prepare features for training
            feature_columns = ['month_ordinal', 'month_num', 'quarter', 'is_q4', 'is_q1',
                             'win_rate', 'customer_supplier_ratio', 'deal_count', 'active_products',
                             'mrc_ma3', 'nrc_ma3', 'mrc_ma6', 'mrc_growth', 'nrc_growth',
                             'mrc_lag1', 'nrc_lag1']
            
            X = featured_data[feature_columns].fillna(0)
            y_mrc = featured_data['total_mrc']
            y_nrc = featured_data['total_nrc']
            
            if len(X) >= 3:  # Minimum 3 data points
                self.mrc_model.fit(X, y_mrc)
                self.nrc_model.fit(X, y_nrc)
                self.is_trained = True
                print(f"✅ Business model trained on {len(X)} data points")
                print(f"📊 Average monthly MRC: ${self.training_stats['avg_mrc']:,.2f}")
                print(f"💰 Average monthly NRC: ${self.training_stats['avg_nrc']:,.2f}")
            else:
                print("⚠️ Too little historical data (minimum 3 months)")
                self.is_trained = False
                
        except Exception as e:
            print(f"❌ Error during model training: {e}")
            self.is_trained = False

    def predict(self, months_ahead: int = 3):
        """Generates business predictions for future months."""
        if not self.is_trained:
            return "Prediction model not trained or no historical data available."

        try:
            predictions = {}
            last_date = pd.to_datetime(self.last_training_date)
            
            for i in range(1, months_ahead + 1):
                future_date = last_date + pd.DateOffset(months=i)
                
                # Prepare features for future date
                features = {
                    'month_ordinal': future_date.toordinal(),
                    'month_num': future_date.month,
                    'quarter': future_date.quarter,
                    'is_q4': 1 if future_date.quarter == 4 else 0,
                    'is_q1': 1 if future_date.quarter == 1 else 0,
                    'win_rate': 0.7,  # Baseline assumption
                    'customer_supplier_ratio': 2.0,  # Baseline assumption
                    'deal_count': self.training_stats.get('avg_mrc', 0) / 1000,  # Estimation
                    'active_products': 50,  # Baseline assumption
                    'mrc_ma3': self.training_stats.get('avg_mrc', 0),
                    'nrc_ma3': self.training_stats.get('avg_nrc', 0),
                    'mrc_ma6': self.training_stats.get('avg_mrc', 0),
                    'mrc_growth': 0.05,  # 5% growth m/m
                    'nrc_growth': 0.02,  # 2% growth m/m
                    'mrc_lag1': self.training_stats.get('avg_mrc', 0),
                    'nrc_lag1': self.training_stats.get('avg_nrc', 0)
                }
                
                X_future = pd.DataFrame([features])
                
                # Predictions
                mrc_pred = max(0, self.mrc_model.predict(X_future)[0])
                nrc_pred = max(0, self.nrc_model.predict(X_future)[0])
                total_pred = mrc_pred + nrc_pred
                
                predictions[future_date.strftime('%Y-%m')] = {
                    'MRC (Monthly Recurring Revenue)': round(mrc_pred, 2),
                    'NRC (Non-Recurring Revenue)': round(nrc_pred, 2),
                    'Total Predicted Revenue': round(total_pred, 2)
                }
            
            return predictions
            
        except Exception as e:
            return f"Error during prediction generation: {e}"

# Initialize advanced business prediction model
prediction_model = BusinessRevenuePredictionModel()

# --- 4. LLM and RAG (Retrieval Augmented Generation) Configuration ---
# Initialize LLM (using OpenAI, according to DEFAULT_LLM_PROVIDER in .env)
llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), temperature=0)

# Initialize embeddings - crucial for RAG
embeddings_model = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))

# RAG documents - database schema description and guidelines
# This information helps the agent understand your database structure and how to interact with it.
rag_documents = [
    "Table 'accounts_account' contains account information (customers and suppliers): id, description, account_type ('Customer', 'Supplier'), city, country, created_date, name. Column 'account_type' defines the account type.",
    "Table 'quotes_quotecontainer' contains offer and revenue data: uuid (PRIMARY KEY), name, status, created_at, total_mrc_contracted_currency (monthly recurring revenue), total_nrc_contracted_currency (non-recurring revenue), account_id, close_date.",
    "Table 'products_productv2' contains products and services: id, mrc (monthly recurring revenue), nrc (non-recurring revenue), start_date, end_date, status, qty, location_a_id, location_z_id.",
    "For revenue analysis use tables 'quotes_quotecontainer' (columns total_mrc_contracted_currency, total_nrc_contracted_currency) and 'products_productv2' (columns mrc, nrc). MRC is monthly recurring revenue, NRC is non-recurring revenue.",
    "For business predictions the system automatically joins data from quotes_quotecontainer, products_productv2 and accounts_account, analyzing MRC/NRC trends, transaction count and account types.",
    "Table 'accounts_account_industries' connects accounts with industries through account_id and accountindustry_id.",
    "Table 'accounts_supplierteam' contains supplier teams: id, account_id, leader_id, is_primary, product_templatev2_id, region_id.",
    "To find a supplier's name and details, join 'accounts_supplierteam' with 'accounts_account' on 'accounts_supplierteam.account_id' = 'accounts_account.id'. Filter for accounts where account_type = 'Supplier'.",
    "To calculate MRC or NRC for a specific supplier, you need to join 'accounts_account' with 'quotes_quotecontainer' on 'accounts_account.id' = 'quotes_quotecontainer.account_id' and filter by the supplier's name or ID.",
    "The 'accounts_supplierteam' table links suppliers to specific products or regions. 'is_primary' field marks the main team for an account.",
    "For queries about 'latest transactions' use quotes_quotecontainer sorting by created_at DESC. For 'active products' use products_productv2 with condition status='active'."
    "Date columns: accounts_account.created_date, quotes_quotecontainer.created_at/close_date, products_productv2.start_date/end_date.",
    "Status in quotes_quotecontainer can be: 'active', 'closed_won', 'closed_lost'. Status in products_productv2 can be: 'active', 'inactive', 'new'."
]

# Creating FAISS vector database from rag_documents and retriever
# FAISS allows for fast searching of most similar documents
vectorstore = FAISS.from_texts(rag_documents, embeddings_model)
retriever = vectorstore.as_retriever()

# Creating RAG tool for the agent
# This tool will allow the agent to access context stored in the vector database
rag_tool = create_retriever_tool(
    retriever,
    name="database_context_retriever",
    description="Use this tool to retrieve additional context about database schema, frequently asked questions, or guidelines regarding SQL queries and predictions."
)

# --- 5. Langchain SQL Agent Configuration ---
# Initialize SQLDatabase for Langchain
# Langchain automatically introspects your database schema
db = SQLDatabase.from_uri(DATABASE_URI)

# Langchain toolkit for SQLDatabase interaction
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

# Add RAG tool to tools available for the agent
# Agent will be able to use both SQL tools (e.g. for schema description, query execution)
# and our RAG tool.
tools = toolkit.get_tools() + [rag_tool]

# Custom system prompt for the agent
# This is crucial for the agent to know what it can do and how to behave.
# Prompt instructions are guidelines for the LLM.
custom_agent_prompt = PromptTemplate.from_template(
    """You are an advanced AI agent that can communicate with PostgreSQL databases and execute SQL queries.
    You also have predictive capabilities for numerical data, such as sales.

    Your tasks:
    1.  **Query Interpretation:** Carefully analyze user intentions.
    2.  **SQL Generation:** If the user asks about database data, generate correct and efficient SQL queries. Always check table schema using the `sql_db_schema` tool before generating complex queries.
    3.  **Predictions:** If the user asks about forecasts (e.g., "how much will be", "forecast for", "predict sales"), activate the internal prediction module. For this purpose, you must first retrieve appropriate historical data from the database (e.g., 'sale_date' and 'amount' from the 'sales' table), then return it to the user in a format suitable for prediction.
    4.  **Context Usage (RAG):** Use the `database_context_retriever` tool to retrieve additional context about database schema, frequently asked questions, or guidelines regarding SQL queries and predictions. This tool is particularly helpful when you need additional information about table structure or how to formulate questions.
    5.  **Responses:** Formulate clear, concise, and helpful responses for the user.

    Remember to always strive to solve the user's problem in the most efficient way, using available tools.

    User question: {input}
    """
)

# Creating SQL agent with tools and custom prompt
# `agent_type="openai-tools"` uses newer OpenAI model capabilities for better tool usage.
agent_executor = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True, # Enable verbose to see how the agent "thinks" and uses tools
    agent_type="openai-tools",
    extra_tools=[rag_tool], # Add our custom RAG tool
    agent_executor_kwargs={"handle_parsing_errors": True}, # Helps debug LLM response parsing errors
    # If you want custom_agent_prompt to replace the default, use:
    # agent_executor_kwargs={"prompt": custom_agent_prompt, "handle_parsing_errors": True}
)

# --- 6. Main User Query Handling Logic ---
def handle_user_query(query: str):
    """
    Handles user queries, distinguishing between SQL queries and predictions.
    """
    query_lower = query.lower()

    # Advanced heuristics for detecting business prediction queries
    # Detects various forms of queries about forecasts, revenue and predictions
    prediction_keywords = ["przewiduj", "prognoza", "ile będzie", "forecast", "predict", "projection", 
                          "przychód", "revenue", "sprzedaż", "sales", "trends", "future"]
    
    if any(keyword in query_lower for keyword in prediction_keywords):
        print("\n--- 🔮 Business prediction query detected ---")
        try:
            conn = get_db_connection()
            if conn:
                # Fetch real business data from the database
                business_data = prediction_model.fetch_business_data(conn)
                conn.close()

                if business_data is not None and not business_data.empty:
                    # Train advanced business model
                    prediction_model.train(business_data)

                    # Determine prediction period based on query
                    months_ahead = 3  # Default 3 months
                    if "kwartał" in query_lower or "quarter" in query_lower:
                        months_ahead = 3
                    elif "rok" in query_lower or "year" in query_lower:
                        months_ahead = 12
                    elif "miesiąc" in query_lower or "month" in query_lower:
                        months_ahead = 1
                    elif "6 miesięcy" in query_lower or "półrocze" in query_lower:
                        months_ahead = 6
                    
                    predictions = prediction_model.predict(months_ahead)
                    
                    if isinstance(predictions, dict):
                        # Format response in a friendly way
                        response = f"📊 **Business Revenue Forecast for {months_ahead} months**\n\n"
                        
                        total_forecasted_mrc = 0
                        total_forecasted_nrc = 0
                        total_forecasted_revenue = 0
                        
                        for month, data in predictions.items():
                            mrc = data['MRC (Monthly Recurring Revenue)']
                            nrc = data['NRC (Non-Recurring Revenue)']
                            total = data['Total Predicted Revenue']
                            
                            total_forecasted_mrc += mrc
                            total_forecasted_nrc += nrc  
                            total_forecasted_revenue += total
                            
                            response += f"📅 **{month}:**\n"
                            response += f"   • MRC (Monthly): ${mrc:,.2f}\n"
                            response += f"   • NRC (One-time): ${nrc:,.2f}\n"
                            response += f"   • Total: ${total:,.2f}\n\n"
                        
                        response += f"💰 **Forecast Summary:**\n"
                        response += f"   • Total forecasted MRC: ${total_forecasted_mrc:,.2f}\n"
                        response += f"   • Total forecasted NRC: ${total_forecasted_nrc:,.2f}\n"
                        response += f"   • **Total forecasted revenue: ${total_forecasted_revenue:,.2f}**\n\n"
                        
                        if hasattr(prediction_model, 'training_stats') and prediction_model.training_stats:
                            stats = prediction_model.training_stats
                            response += f"📈 **Baseline data (based on {stats.get('data_points', 0)} months):**\n"
                            response += f"   • Average monthly MRC: ${stats.get('avg_mrc', 0):,.2f}\n"
                            response += f"   • Average monthly NRC: ${stats.get('avg_nrc', 0):,.2f}\n"
                            response += f"   • Analysis period: {stats.get('date_range', 'N/A')}\n"
                        
                        return response
                    else:
                        return f"❌ Problem generating predictions: {predictions}"
                        
                else:
                    return "⚠️ Insufficient business data to perform predictions. System analyzes data from 'quotes_quotecontainer' and 'products_productv2' tables from the last 24 months."
            else:
                return "❌ Failed to connect to database to fetch business data. Check connection configuration."

        except Exception as e:
            return f"❌ Error occurred during predictive analysis: {e}\n\nTry asking about specific business data instead of predictions."
    try:
        # Pass query to Langchain SQL agent
        print("\n--- Processing SQL query using the agent ---")
        result = agent_executor.invoke({"input": query})
        return result.get("output", "Could not find an answer to your query.")
    except Exception as e:
        error_message = f"Error during initial query execution: {e}"
        print(error_message)

        # Attempt to fix the query
        # For this, we would need to extract the failed SQL query from the agent's verbose output
        # or by other means. This is a conceptual implementation.
        # Let's assume we have a way to get the last `failed_query`.
        failed_query = "" # Placeholder
        db_schema = db.get_table_info() # Get current schema to help with fixing
        
        fixed_sql = attempt_to_fix_sql(failed_query, str(e), db_schema)
        
        if fixed_sql:
            print("\n--- 🔁 Retrying with fixed SQL query ---")
            try:
                # We would need a way to execute the raw SQL and return the result.
                # The current agent setup doesn't expose this directly, so we'd typically
                # need to adjust the agent or use a separate DB connection.
                # For now, we can try invoking the agent again with a more direct prompt.
                new_prompt = f"Please execute this SQL query and return the result: {fixed_sql}"
                result = agent_executor.invoke({"input": new_prompt})
                return result.get("output", "Successfully executed the fixed query, but no result was returned.")
            except Exception as retry_e:
                return f"❌ The fixed query also failed: {retry_e}"
        else:
            return "I could not fix the SQL query. Please rephrase your question."

# --- 7. Main Program Loop (User Interaction) ---
if __name__ == "__main__":
    print("--- SQL AI Agent with prediction functionality ready! ---")
    print("Enter your query (e.g., 'Show me 5 latest transactions' or 'Predict sales for next 3 months').")
    print("Type 'exit' to quit.")

    # Test database connection at application startup
    test_conn = get_db_connection()
    if test_conn:
        test_conn.close()
        print("Test database connection completed successfully.")
    else:
        print("Failed to establish test database connection. Check configuration in .env and RDS availability.")
        exit() # Exit program if database connection doesn't work

    while True:
        user_input = input("\nYour query: ")
        if user_input.lower() == 'exit':
            print("Agent operation completed.")
            break
        
        response = handle_user_query(user_input)
        print(f"\n--- Agent Response ---\n{response}")