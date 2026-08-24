# redis_state_manager.py
import redis
import json
from datetime import datetime
from typing import Optional, Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisStateManager:
    """Manages meter state persistence in Redis per SRS FE-5"""
    
    def __init__(self, host='localhost', port=6379, db=0):
        try:
            self.redis = redis.Redis(
                host=host, port=port, db=db,
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.redis.ping()
            logger.info(f"✅ Redis connected at {host}:{port}")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.redis = None
    
    def update_meter_state(self, meter_id: str, tier: str, risk_score: float, 
                          details: Dict = None) -> bool:
        """Update meter state (persistent, TTL -1)"""
        if not self.redis:
            return False
        
        try:
            state = {
                'tier': tier,
                'risk_score': float(risk_score),
                'last_seen': datetime.utcnow().isoformat(),
                'isolation_since': details.get('isolation_since') if details else None,
                'details': json.dumps(details) if details else '{}'
            }
            
            key = f'meter:state:{meter_id}'
            self.redis.set(key, json.dumps(state), ex=None)
            logger.info(f"✅ Updated state: {meter_id} → {tier} (risk={risk_score:.1%})")
            return True
        except Exception as e:
            logger.error(f"❌ State update failed: {e}")
            return False
    
    def get_meter_state(self, meter_id: str) -> Optional[Dict]:
        """Retrieve meter's current state"""
        if not self.redis:
            return None
        
        try:
            key = f'meter:state:{meter_id}'
            data = self.redis.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"❌ Failed to get state: {e}")
            return None
    
    def get_all_meter_states(self) -> Dict[str, Dict]:
        """Retrieve all meter states"""
        if not self.redis:
            return {}
        
        try:
            all_states = {}
            cursor = 0
            while True:
                cursor, keys = self.redis.scan(cursor, match='meter:state:*', count=100)
                for key in keys:
                    meter_id = key.replace('meter:state:', '')
                    data = self.redis.get(key)
                    if data:
                        all_states[meter_id] = json.loads(data)
                if cursor == 0:
                    break
            return all_states
        except Exception as e:
            logger.error(f"❌ Failed to get all states: {e}")
            return {}
    
    def cache_risk_score(self, meter_id: str, risk_score: float, ttl_seconds: int = 90) -> bool:
        """Cache risk score (expires after 90s per SDS 3.9)"""
        if not self.redis:
            return False
        
        try:
            key = f'meter:risk:{meter_id}'
            self.redis.set(key, str(float(risk_score)), ex=ttl_seconds)
            logger.debug(f"📊 Cached risk: {meter_id} = {risk_score:.1%} (TTL {ttl_seconds}s)")
            return True
        except Exception as e:
            logger.error(f"❌ Cache risk failed: {e}")
            return False
    
    def get_cached_risk_score(self, meter_id: str) -> Optional[float]:
        """Retrieve cached risk score"""
        if not self.redis:
            return None
        try:
            key = f'meter:risk:{meter_id}'
            value = self.redis.get(key)
            return float(value) if value else None
        except Exception as e:
            return None
    
    def mark_meter_isolated(self, meter_id: str, isolation_start: str = None) -> bool:
        """Mark meter as isolated"""
        if not self.redis:
            return False
        
        try:
            key = f'meter:isolation:{meter_id}'
            timestamp = isolation_start or datetime.utcnow().isoformat()
            self.redis.set(key, json.dumps({'isolated_since': timestamp}), ex=None)
            logger.info(f"🔒 Marked isolated: {meter_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Mark isolated failed: {e}")
            return False
    
    def clear_meter_isolation(self, meter_id: str) -> bool:
        """Clear isolation marker"""
        if not self.redis:
            return False
        try:
            key = f'meter:isolation:{meter_id}'
            self.redis.delete(key)
            logger.info(f"🔓 Cleared isolation: {meter_id}")
            return True
        except Exception as e:
            return False
    
    def get_isolated_meters(self) -> List[str]:
        """Get list of isolated meters"""
        if not self.redis:
            return []
        
        try:
            isolated = []
            cursor = 0
            while True:
                cursor, keys = self.redis.scan(cursor, match='meter:isolation:*', count=100)
                for key in keys:
                    meter_id = key.replace('meter:isolation:', '')
                    isolated.append(meter_id)
                if cursor == 0:
                    break
            return isolated
        except Exception as e:
            logger.error(f"❌ Failed to get isolated: {e}")
            return []
    
    def get_tier_distribution(self) -> Dict[str, int]:
        """Get count of meters in each tier"""
        distribution = {'LOG': 0, 'ALERT': 0, 'RATE_LIMIT': 0, 'FULL_ISOLATION': 0}
        all_states = self.get_all_meter_states()
        
        for state in all_states.values():
            tier = state.get('tier', 'LOG')
            if tier in distribution:
                distribution[tier] += 1
        
        return distribution
    
    def get_system_metrics(self) -> Dict:
        """Get system-wide metrics for Prometheus"""
        try:
            all_states = self.get_all_meter_states()
            isolated = self.get_isolated_meters()
            
            total = len(all_states)
            high_risk = sum(1 for s in all_states.values() if s.get('risk_score', 0) > 0.8)
            critical = sum(1 for s in all_states.values() if s.get('risk_score', 0) > 0.95)
            avg_risk = sum(s.get('risk_score', 0) for s in all_states.values()) / total if total else 0
            
            return {
                'total_meters': total,
                'meters_per_tier': self.get_tier_distribution(),
                'isolation_count': len(isolated),
                'average_risk_score': avg_risk,
                'high_risk_count': high_risk,
                'critical_count': critical,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Failed to get metrics: {e}")
            return {}
    
    def clear_meter_data(self, meter_id: str) -> bool:
        """Clear all Redis data for a meter"""
        if not self.redis:
            return False
        try:
            self.redis.delete(
                f'meter:state:{meter_id}',
                f'meter:risk:{meter_id}',
                f'meter:isolation:{meter_id}'
            )
            logger.info(f"🗑️  Cleared data: {meter_id}")
            return True
        except Exception as e:
            return False
