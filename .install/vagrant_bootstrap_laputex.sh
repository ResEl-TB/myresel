#!/usr/bin/env bash

echo ">>> Updating system <<<"
apt-get -qq update
apt-get -qq upgrade

echo '>>> downloading last version of laputex <<<'
apt-get -qq install git
# export GIT_SSH_COMMAND='ssh -i /myresel/.install/lib/id_rsa_local_dev_env -o StrictHostKeyChecking=no'

export GIT_SSH=/tmp/git_ssh
cat >/tmp/git_ssh <<EOF
#!/bin/bash
ssh -i /myresel/.install/lib/id_rsa_local_dev_env -o StrictHostKeyChecking=no "\$@"
EOF
chmod 755 /tmp/git_ssh

if cd /laputex; 
then 
    git pull; 
else 
    git clone ssh://git@git.resel.fr:43000/resel/LaPuTeX.git /laputex; 
fi

echo ">>> Executing laputex installation script <<<"
cd /laputex
chmod -R +x /laputex/.install/
/laputex/.install/bootstrap.sh

#echo ">>> Create a configuration file <<<"
