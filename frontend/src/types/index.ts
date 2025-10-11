export interface User {
    username: string;
  }
  
  export interface AuthState {
    token: string | null;
    user: User | null;
    isAuthenticated: boolean;
  }
  
  export interface Prediction {
    id: number;
    machine_id: string;
    part_id: string;
    prediction_score: number;
    prediction_timestamp: string;
  }
  
  export interface PredictionRequest {
    machine_id: string;
    part_id: string;
    time_in_service_days: number;
  }