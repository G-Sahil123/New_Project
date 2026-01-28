# models/folder_mysql.py
import uuid
from typing import Optional, List
from models.document import FolderCreate, FolderResponse
from models.users import MySQLDatabase

class FolderManager:
    def __init__(self, db_connection: MySQLDatabase):
        self.db = db_connection

    def create_folder(self, user_id: str, folder_data: FolderCreate) -> FolderResponse:
        """Create a new folder"""
        folder_id = str(uuid.uuid4())
        
        query = """
        INSERT INTO document_folders (id, user_id, name)
        VALUES (%s, %s, %s)
        """
        
        self.db.execute_query(
            query, 
            (folder_id, user_id, folder_data.name),
            fetch=False
        )
        
        # Get the created folder
        return self.get_folder(folder_id, user_id)

    def get_folder(self, folder_id: str, user_id: str) -> Optional[FolderResponse]:
        """Get folder by ID"""
        query = """
        SELECT f.*, COUNT(d.id) as document_count
        FROM document_folders f
        LEFT JOIN processed_documents d ON f.id = d.folder_id AND d.user_id = f.user_id
        WHERE f.id = %s AND f.user_id = %s
        GROUP BY f.id
        """
        
        result = self.db.execute_query(query, (folder_id, user_id))
        
        if not result:
            return None
        folder_data = dict(result[0])
        return FolderResponse(**folder_data)

    def get_user_folders(self, user_id: str) -> List[FolderResponse]:
        """Get all folders for a user with document counts"""
        query = """
        SELECT 
            f.*,
            COUNT(d.id) as document_count
        FROM document_folders f
        LEFT JOIN processed_documents d ON f.id = d.folder_id AND d.user_id = f.user_id
        WHERE f.user_id = %s
        GROUP BY f.id
        ORDER BY f.name
        """
        
        result = self.db.execute_query(query, (user_id,))
        
        folders = []
        for row in result:
            # ✅ Convert each row to dictionary
            folder_data = dict(row)
            folders.append(FolderResponse(**folder_data))
        
        return folders

    def update_folder(self, folder_id: str, user_id: str, 
                     name: str) -> Optional[FolderResponse]:
        """Update folder name"""
        query = """
        UPDATE document_folders 
        SET name = %s
        WHERE id = %s AND user_id = %s
        """
        
        self.db.execute_query(
            query, 
            (name, folder_id, user_id),
            fetch=False
        )
        
        # Check if update was successful and return updated folder
        return self.get_folder(folder_id, user_id)

    def delete_folder(self, folder_id: str, user_id: str, 
                     move_to_folder_id: Optional[str] = None) -> bool:
        """Delete folder and handle documents"""
        # First, move documents to another folder or set to NULL
        if move_to_folder_id:
            update_query = """
            UPDATE processed_documents 
            SET folder_id = %s 
            WHERE folder_id = %s AND user_id = %s
            """
            self.db.execute_query(update_query, (move_to_folder_id, folder_id, user_id), fetch=False)
        else:
            # Set documents to no folder
            update_query = """
            UPDATE processed_documents 
            SET folder_id = NULL 
            WHERE folder_id = %s AND user_id = %s
            """
            self.db.execute_query(update_query, (folder_id, user_id), fetch=False)
        
        # Delete the folder
        delete_query = "DELETE FROM document_folders WHERE id = %s AND user_id = %s"
        self.db.execute_query(delete_query, (folder_id, user_id), fetch=False)
        
        check_query = "SELECT ROW_COUNT()"
        result = self.db.execute_query(check_query)
        
        if result:
            # Convert to dictionary and access the value
            row_dict = dict(result[0])
            return list(row_dict.values())[0] > 0
        return False