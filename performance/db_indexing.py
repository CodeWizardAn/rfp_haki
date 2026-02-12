"""
Database Indexing Management

Index management and optimization with:
- Index analysis and recommendations
- Automatic index creation
- Unused index detection
- Index health monitoring
"""

import re
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class IndexType(Enum):
    """Types of database indexes"""
    BTREE = "btree"
    HASH = "hash"
    GIN = "gin"  # Generalized Inverted Index (PostgreSQL)
    GIST = "gist"  # Generalized Search Tree
    BRIN = "brin"  # Block Range Index
    FULLTEXT = "fulltext"
    SPATIAL = "spatial"


@dataclass
class IndexInfo:
    """Information about a database index"""
    name: str
    table_name: str
    columns: List[str]
    index_type: IndexType = IndexType.BTREE
    is_unique: bool = False
    is_primary: bool = False
    is_partial: bool = False
    size_bytes: int = 0
    created_at: Optional[datetime] = None
    
    # Usage statistics
    scans: int = 0
    tuples_read: int = 0
    tuples_fetched: int = 0
    last_used: Optional[datetime] = None


@dataclass
class IndexRecommendation:
    """Recommended index to create"""
    table_name: str
    columns: List[str]
    index_type: IndexType = IndexType.BTREE
    reason: str = ""
    estimated_improvement: float = 0.0  # Percentage improvement
    priority: int = 1  # 1=high, 2=medium, 3=low
    create_statement: str = ""
    
    def generate_create_statement(self, index_name: str = None) -> str:
        """Generate CREATE INDEX statement"""
        if not index_name:
            columns_str = "_".join(self.columns)
            index_name = f"idx_{self.table_name}_{columns_str}"
        
        columns_list = ", ".join(self.columns)
        
        if self.index_type == IndexType.BTREE:
            return f"CREATE INDEX {index_name} ON {self.table_name} ({columns_list});"
        elif self.index_type == IndexType.GIN:
            return f"CREATE INDEX {index_name} ON {self.table_name} USING gin ({columns_list});"
        elif self.index_type == IndexType.HASH:
            return f"CREATE INDEX {index_name} ON {self.table_name} USING hash ({columns_list});"
        else:
            return f"CREATE INDEX {index_name} ON {self.table_name} ({columns_list});"


class IndexManager:
    """
    Database index management and optimization
    """
    
    def __init__(self, session_factory=None):
        """
        Initialize index manager
        
        Args:
            session_factory: SQLAlchemy session factory
        """
        self.session_factory = session_factory
        
        # Cache of known indexes
        self._indexes: Dict[str, IndexInfo] = {}
        
        # Query patterns for analysis
        self._query_patterns: Dict[str, Dict[str, Any]] = {}
        
        logger.info("IndexManager initialized")
    
    def analyze_query_for_indexes(self, query: str) -> List[IndexRecommendation]:
        """
        Analyze a query and recommend indexes
        
        Args:
            query: SQL query to analyze
            
        Returns:
            List of index recommendations
        """
        recommendations = []
        
        # Extract table and columns from WHERE clause
        where_columns = self._extract_where_columns(query)
        join_columns = self._extract_join_columns(query)
        order_columns = self._extract_order_columns(query)
        
        # Recommend indexes for WHERE columns
        for table, columns in where_columns.items():
            # Single column indexes
            for col in columns:
                rec = IndexRecommendation(
                    table_name=table,
                    columns=[col],
                    reason=f"Used in WHERE clause",
                    priority=1
                )
                rec.create_statement = rec.generate_create_statement()
                recommendations.append(rec)
            
            # Composite index for multiple WHERE columns
            if len(columns) > 1:
                rec = IndexRecommendation(
                    table_name=table,
                    columns=list(columns),
                    reason=f"Composite index for WHERE conditions",
                    priority=2
                )
                rec.create_statement = rec.generate_create_statement()
                recommendations.append(rec)
        
        # Recommend indexes for JOIN columns
        for table, columns in join_columns.items():
            for col in columns:
                rec = IndexRecommendation(
                    table_name=table,
                    columns=[col],
                    reason=f"Used in JOIN condition",
                    priority=1
                )
                rec.create_statement = rec.generate_create_statement()
                recommendations.append(rec)
        
        # Recommend indexes for ORDER BY
        for table, columns in order_columns.items():
            if columns:
                rec = IndexRecommendation(
                    table_name=table,
                    columns=list(columns),
                    reason=f"Used in ORDER BY",
                    priority=2
                )
                rec.create_statement = rec.generate_create_statement()
                recommendations.append(rec)
        
        return recommendations
    
    def _extract_where_columns(self, query: str) -> Dict[str, Set[str]]:
        """Extract columns used in WHERE clause"""
        result = {}
        
        # Find WHERE clause
        where_match = re.search(r'\bWHERE\b(.+?)(?:\bORDER\b|\bGROUP\b|\bLIMIT\b|\bHAVING\b|$)', 
                               query, re.IGNORECASE | re.DOTALL)
        if not where_match:
            return result
        
        where_clause = where_match.group(1)
        
        # Extract table.column or just column patterns
        patterns = re.findall(r'(\w+)\.(\w+)\s*[=<>]|(\w+)\s*[=<>]', where_clause)
        
        for match in patterns:
            if match[0] and match[1]:  # table.column pattern
                table = match[0]
                column = match[1]
            elif match[2]:  # just column
                table = self._infer_table_from_query(query, match[2])
                column = match[2]
            else:
                continue
            
            if table not in result:
                result[table] = set()
            result[table].add(column)
        
        return result
    
    def _extract_join_columns(self, query: str) -> Dict[str, Set[str]]:
        """Extract columns used in JOIN conditions"""
        result = {}
        
        # Find JOIN ON clauses
        join_matches = re.findall(
            r'\bJOIN\s+(\w+)\s+(?:\w+\s+)?ON\s+(.+?)(?:\bJOIN\b|\bWHERE\b|\bORDER\b|$)',
            query, re.IGNORECASE
        )
        
        for table, condition in join_matches:
            columns = re.findall(r'(\w+)\.(\w+)', condition)
            for tbl, col in columns:
                if tbl.lower() == table.lower():
                    if table not in result:
                        result[table] = set()
                    result[table].add(col)
        
        return result
    
    def _extract_order_columns(self, query: str) -> Dict[str, Set[str]]:
        """Extract columns used in ORDER BY"""
        result = {}
        
        order_match = re.search(r'\bORDER\s+BY\b(.+?)(?:\bLIMIT\b|$)', 
                               query, re.IGNORECASE)
        if not order_match:
            return result
        
        order_clause = order_match.group(1)
        
        # Extract columns
        columns = re.findall(r'(\w+)(?:\s+(?:ASC|DESC))?', order_clause)
        
        if columns:
            table = self._infer_table_from_query(query, columns[0])
            result[table] = set(columns)
        
        return result
    
    def _infer_table_from_query(self, query: str, column: str) -> str:
        """Try to infer table name from query context"""
        # Get primary table from FROM clause
        from_match = re.search(r'\bFROM\s+(\w+)', query, re.IGNORECASE)
        if from_match:
            return from_match.group(1)
        
        # Get table from UPDATE
        update_match = re.search(r'\bUPDATE\s+(\w+)', query, re.IGNORECASE)
        if update_match:
            return update_match.group(1)
        
        return "unknown"
    
    def get_existing_indexes(self, engine=None) -> List[IndexInfo]:
        """
        Get all existing indexes from database
        
        Args:
            engine: SQLAlchemy engine
            
        Returns:
            List of IndexInfo objects
        """
        if not engine and not self.session_factory:
            return []
        
        indexes = []
        
        try:
            # PostgreSQL query for indexes
            query = """
                SELECT
                    i.relname as index_name,
                    t.relname as table_name,
                    array_agg(a.attname ORDER BY array_position(ix.indkey, a.attnum)) as columns,
                    am.amname as index_type,
                    ix.indisunique as is_unique,
                    ix.indisprimary as is_primary,
                    pg_relation_size(i.oid) as size_bytes
                FROM pg_index ix
                JOIN pg_class i ON i.oid = ix.indexrelid
                JOIN pg_class t ON t.oid = ix.indrelid
                JOIN pg_am am ON am.oid = i.relam
                JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
                WHERE t.relkind = 'r'
                GROUP BY i.relname, t.relname, am.amname, ix.indisunique, ix.indisprimary, i.oid
            """
            
            eng = engine or (self.session_factory().get_bind() if self.session_factory else None)
            if eng:
                result = eng.execute(query)
                for row in result:
                    index_type = IndexType.BTREE
                    if row['index_type'] == 'hash':
                        index_type = IndexType.HASH
                    elif row['index_type'] == 'gin':
                        index_type = IndexType.GIN
                    
                    indexes.append(IndexInfo(
                        name=row['index_name'],
                        table_name=row['table_name'],
                        columns=list(row['columns']),
                        index_type=index_type,
                        is_unique=row['is_unique'],
                        is_primary=row['is_primary'],
                        size_bytes=row['size_bytes']
                    ))
                    
        except Exception as e:
            logger.warning(f"Could not fetch indexes: {e}")
        
        return indexes
    
    def get_unused_indexes(self, engine=None, min_age_days: int = 7) -> List[IndexInfo]:
        """
        Find indexes that haven't been used recently
        
        Args:
            engine: SQLAlchemy engine
            min_age_days: Minimum age of index to consider
            
        Returns:
            List of unused IndexInfo objects
        """
        unused = []
        
        try:
            # PostgreSQL query for index usage stats
            query = """
                SELECT
                    schemaname,
                    relname as table_name,
                    indexrelname as index_name,
                    idx_scan as scans,
                    idx_tup_read as tuples_read,
                    idx_tup_fetch as tuples_fetched,
                    pg_relation_size(indexrelid) as size_bytes
                FROM pg_stat_user_indexes
                WHERE idx_scan = 0
                ORDER BY pg_relation_size(indexrelid) DESC
            """
            
            eng = engine or (self.session_factory().get_bind() if self.session_factory else None)
            if eng:
                result = eng.execute(query)
                for row in result:
                    unused.append(IndexInfo(
                        name=row['index_name'],
                        table_name=row['table_name'],
                        columns=[],  # Would need additional query
                        scans=row['scans'],
                        tuples_read=row['tuples_read'],
                        tuples_fetched=row['tuples_fetched'],
                        size_bytes=row['size_bytes']
                    ))
                    
        except Exception as e:
            logger.warning(f"Could not fetch index usage: {e}")
        
        return unused
    
    def get_duplicate_indexes(self) -> List[Tuple[IndexInfo, IndexInfo]]:
        """
        Find duplicate or redundant indexes
        
        Returns:
            List of tuples containing duplicate index pairs
        """
        duplicates = []
        
        indexes = list(self._indexes.values())
        
        for i, idx1 in enumerate(indexes):
            for idx2 in indexes[i+1:]:
                if idx1.table_name != idx2.table_name:
                    continue
                
                # Check if columns are subset
                cols1 = set(idx1.columns)
                cols2 = set(idx2.columns)
                
                if cols1 == cols2:
                    duplicates.append((idx1, idx2))
                elif cols1.issubset(cols2) and idx1.index_type == idx2.index_type:
                    duplicates.append((idx1, idx2))
                elif cols2.issubset(cols1) and idx1.index_type == idx2.index_type:
                    duplicates.append((idx2, idx1))
        
        return duplicates
    
    def create_index(self, recommendation: IndexRecommendation, 
                     engine=None, concurrently: bool = True) -> bool:
        """
        Create an index based on recommendation
        
        Args:
            recommendation: Index recommendation
            engine: SQLAlchemy engine
            concurrently: Create index concurrently (PostgreSQL)
            
        Returns:
            True if successful
        """
        try:
            statement = recommendation.create_statement
            
            if concurrently and 'CREATE INDEX' in statement:
                statement = statement.replace('CREATE INDEX', 'CREATE INDEX CONCURRENTLY')
            
            eng = engine or (self.session_factory().get_bind() if self.session_factory else None)
            if eng:
                # Need to execute outside transaction for CONCURRENTLY
                connection = eng.connect()
                connection.execute("COMMIT")  # End any transaction
                connection.execute(statement)
                logger.info(f"Created index: {statement}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
        
        return False
    
    def drop_index(self, index_name: str, engine=None, 
                   concurrently: bool = True) -> bool:
        """
        Drop an index
        
        Args:
            index_name: Name of index to drop
            engine: SQLAlchemy engine
            concurrently: Drop concurrently (PostgreSQL)
            
        Returns:
            True if successful
        """
        try:
            if concurrently:
                statement = f"DROP INDEX CONCURRENTLY IF EXISTS {index_name}"
            else:
                statement = f"DROP INDEX IF EXISTS {index_name}"
            
            eng = engine or (self.session_factory().get_bind() if self.session_factory else None)
            if eng:
                connection = eng.connect()
                connection.execute("COMMIT")
                connection.execute(statement)
                logger.info(f"Dropped index: {index_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to drop index: {e}")
        
        return False
    
    def analyze_table(self, table_name: str, engine=None) -> Dict[str, Any]:
        """
        Analyze table for index recommendations
        
        Args:
            table_name: Table to analyze
            engine: SQLAlchemy engine
            
        Returns:
            Analysis results with recommendations
        """
        analysis = {
            'table': table_name,
            'existing_indexes': [],
            'recommendations': [],
            'unused_indexes': [],
            'duplicate_indexes': []
        }
        
        # Get existing indexes
        all_indexes = self.get_existing_indexes(engine)
        analysis['existing_indexes'] = [
            idx for idx in all_indexes 
            if idx.table_name == table_name
        ]
        
        # Get unused indexes
        unused = self.get_unused_indexes(engine)
        analysis['unused_indexes'] = [
            idx for idx in unused 
            if idx.table_name == table_name
        ]
        
        return analysis
    
    def get_index_health_report(self, engine=None) -> Dict[str, Any]:
        """
        Generate comprehensive index health report
        
        Returns:
            Health report with all index statistics
        """
        indexes = self.get_existing_indexes(engine)
        unused = self.get_unused_indexes(engine)
        duplicates = self.get_duplicate_indexes()
        
        total_size = sum(idx.size_bytes for idx in indexes)
        unused_size = sum(idx.size_bytes for idx in unused)
        
        return {
            'total_indexes': len(indexes),
            'total_size_mb': total_size / (1024 * 1024),
            'unused_indexes': len(unused),
            'unused_size_mb': unused_size / (1024 * 1024),
            'duplicate_pairs': len(duplicates),
            'recommendations': [
                f"Drop unused index {idx.name} ({idx.size_bytes / 1024:.1f}KB)"
                for idx in unused[:5]
            ]
        }
