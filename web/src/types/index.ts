export interface Poc {
  id: number
  name: string
  domain: string
  app_name: string
  model_id: number | null
  model_name: string | null
  adapter_path: string | null
  job_count: number
  last_trained_at: string | null
}

export interface TrainingJob {
  id: number
  poc_id: number
  model_id: number
  name: string
  status: number  // 1=draft 2=running 3=done 4=error
  instance_id: string | null
  created_at: string
  started_at: string | null
  finished_at: string | null
  error_message: string | null
  output_model_name: string | null
  log_count: number
  iters: number
  batch_size: number
  learning_rate: number
  num_layers: number
  max_seq_length: number
  training_mode: number  // 1=batch 2=sequential
  loss_threshold: number | null
}

export interface TrainingDataIn {
  log_id: number
  role: number  // 1=train 2=valid
}

export interface Log {
  id: number
  question: string
  answer: string | null
  expected_answer: string | null
  training_role: number | null
  training_role_label: string
  evaluation: number | null
  evaluation_label: string
  timestamp: string
  user_id: number | null
  username: string | null
  is_trained: boolean
  final_loss: number | null
  iterations: number | null
  job_name: string | null
  trained_at: string | null
  training_mode: number | null
  training_data_role: number | null
}

export interface Dataset {
  id: number
  name: string
  description: string | null
}

export interface Model {
  id: number
  model_name: string
  base_model: string | null
  adapter_path: string | null
  parent_model_id: number | null
  description: string | null
  created_at: string
  job_id: number | null
  job_name: string | null
  training_mode: number | null
  job_status: number | null
  executed_at: string | null
  finished_at: string | null
}
