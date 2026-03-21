module.exports = {
  apps: [
    {
      name: 'learn-back-1',
      script: '/Users/mini/dev/llamune_learn/start.sh',
      interpreter: '/bin/bash',
      cwd: '/Users/mini/dev/llamune_learn',
      out_file: '/Users/mini/dev/llamune_learn/logs/learn-back-1.log',
      error_file: '/Users/mini/dev/llamune_learn/logs/learn-back-1.log',
      merge_logs: true,
      env: {
        INSTANCE_ID_ARG: 'learn-back-1',
        PORT: '8100',
      },
    },
  ]
}
