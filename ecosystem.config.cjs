module.exports = {
  apps: [{
    name: 'llamune_learn',
    script: '/Users/mini/dev/llamune_learn/start.sh',
    interpreter: '/bin/bash',
    cwd: '/Users/mini/dev/llamune_learn',
    out_file: '/Users/mini/dev/llamune_learn/logs/learn.log',
    error_file: '/Users/mini/dev/llamune_learn/logs/learn.log',
    merge_logs: true,
  }]
}
