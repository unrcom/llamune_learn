module.exports = {
  apps: [
    {
      name: 'learn-front-1',
      script: 'npm',
      args: 'run dev -- --port 5273 --host',
      cwd: '/Users/mini/dev/llamune_learn/web',
      out_file: '/Users/mini/dev/llamune_learn/logs/learn-front-1.log',
      error_file: '/Users/mini/dev/llamune_learn/logs/learn-front-1.log',
      merge_logs: true,
    },
    {
      name: 'learn-front-2',
      script: 'npm',
      args: 'run dev -- --port 5274 --host',
      cwd: '/Users/mini/dev/llamune_learn/web',
      out_file: '/Users/mini/dev/llamune_learn/logs/learn-front-2.log',
      error_file: '/Users/mini/dev/llamune_learn/logs/learn-front-2.log',
      merge_logs: true,
    },
  ]
}
