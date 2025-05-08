from flask import Flask, request, jsonify
from datetime import datetime
import psycopg2
from psycopg2 import sql
import logging
import json  # Добавлен недостающий импорт
import sys   # Для обработки ошибок

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация БД
DB_CONFIG = {
    "host": "db",
    "port": "5432",
    "database": "microservice_db",
    "user": "postgres",
    "password": "postgres",
    "connect_timeout": 5  # Таймаут подключения
}

def get_db_connection():
    """Установка соединения с БД с обработкой ошибок"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {e}")
        raise

@app.route('/api/process', methods=['POST'])
def process_data():
    conn = None
    try:
        # Логирование входящего запроса
        logger.info(f"Incoming request headers: {request.headers}")
        logger.info(f"Incoming request data: {request.json}")
        
        if not request.json:
            logger.warning("Empty request received")
            return jsonify({"error": "No data provided"}), 400
            
        data = request.json
        
        # Валидация обязательных полей
        if 'name' not in data or 'email' not in data:
            return jsonify({"error": "Missing required fields"}), 400

        # Обработка данных
        processed_data = {
            "original": data,
            "processed": True,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "python-microservice"
        }
        
        # Подключение к БД
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Создание таблицы (если не существует)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_data (
                id SERIAL PRIMARY KEY,
                original_data JSONB NOT NULL,
                processed_data JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                source VARCHAR(100)
            )
        """)
        
        # Сохранение данных с явным указанием типа jsonb
        cursor.execute(
            sql.SQL("""
                INSERT INTO processed_data 
                (original_data, processed_data, source) 
                VALUES (%s::jsonb, %s::jsonb, %s)
                RETURNING id
            """),
            [
                json.dumps(data),
                json.dumps(processed_data),
                'api-process'
            ]
        )
        
        inserted_id = cursor.fetchone()[0]
        conn.commit()
        
        logger.info(f"Data successfully processed and saved with ID: {inserted_id}")
        
        return jsonify({
            "status": "success",
            "id": inserted_id,
            "processed_data": processed_data,
            "database": "postgresql"
        })
        
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        if conn:
            conn.rollback()
        return jsonify({
            "status": "error",
            "type": "database",
            "message": str(e)
        }), 500
        
    except Exception as e:
        logger.error(f"Unexpected error: {sys.exc_info()[0]}")
        return jsonify({
            "status": "error",
            "type": "processing",
            "message": str(e)
        }), 500
        
    finally:
        if conn:
            conn.close()

@app.route('/health', methods=['GET'])
def health():
    try:
        # Проверка соединения с БД
        conn = get_db_connection()
        conn.close()
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    try:
        logger.info("Starting Python microservice...")
        app.run(
            host='0.0.0.0', 
            port=5000, 
            debug=True, 
            threaded=True
        )
    except Exception as e:
        logger.critical(f"Failed to start service: {e}")
        sys.exit(1)