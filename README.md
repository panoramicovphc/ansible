# Playbooks Ansible

Este repositório contém playbooks Ansible para configurar e gerenciar a infraestrutura de diversas soluções do condomínio. O projeto faz parte de uma iniciativa mais ampla de Infraestrutura como Código (IaC) voltada para automatizar a implantação e o gerenciamento de vários serviços e aplicações.

## Visão Geral

Os playbooks neste repositório são projetados para:

- Configurar o ambiente de execução do Ansible.
- Instalar as dependências necessárias para o Ansible.
- Propagar o projeto Ansible para os nós remotos.
- Implantar projetos Docker em nós remotos.

## Playbooks

### setup_ansible_runtime.yml

Este playbook configura o ambiente de execução do Ansible, realizando as seguintes tarefas:

- Garantindo que o script de configuração seja executável.
- Removendo arquivos de log antigos.
- Executando o script de configuração.
- Imprimindo os logs de saída e erro.

### setup_ansible_dependencies.yml

Este playbook instala as dependências necessárias para o Ansible em sistemas baseados em Debian e Red Hat.

### propagate_ansible_project.yml

Este playbook propaga o projeto Ansible para os nós remotos, realizando as seguintes tarefas:

- Criando backups do projeto atual.
- Limpando o diretório de destino.
- Copiando os arquivos do projeto para os nós remotos.
- Definindo permissões apropriadas.

### deploy-docker.yml

Este playbook realiza a implantação de projetos Docker nos nós remotos, incluindo:

- Backup do projeto atual.
- Limpeza do diretório de destino.
- Configuração e inicialização de serviços Docker Compose.
- Instalação do Docker, caso necessário.
- Configuração de redes e volumes Docker.

## Inventário

O arquivo `inventory/hosts.ini` contém a configuração de inventário para os playbooks Ansible. Ele usa variáveis de ambiente para informações sensíveis.

### Indicando Soluções Estruturais

No arquivo de inventário, você pode especificar quais soluções estruturais (como RabbitMQ e Redis) serão servidas por cada host usando o atributo `labels`. Isso permite que várias soluções compartilhem a mesma instância em um host. Por exemplo:

```ini
[prd]
host1    ansible_user=${HOST1_USER_LOGIN}    ansible_password=${HOST1_USER_PASSWORD}    CF_TUNNEL_TOKEN=${CF_TUNNEL_TOKEN_HOST1}    labels='[ "ansible_controller", "rabbitmq" ]'
host2    ansible_user=${HOST2_USER_LOGIN}    ansible_password=${HOST2_USER_PASSWORD}    CF_TUNNEL_TOKEN=${CF_TUNNEL_TOKEN_HOST2}    labels='[ "ansible_controller" ]'

[pc]
host3    ansible_user=${HOST3_USER_LOGIN}    ansible_password=${HOST3_USER_PASSWORD}    CF_TUNNEL_TOKEN=${CF_TUNNEL_TOKEN_HOST3}    labels='[ "open_webui", "tabbyml" ]'
```

## Fluxo de Trabalho do GitHub Actions

O arquivo `.github/workflows/build-n-deploy.yml` contém um fluxo de trabalho do GitHub Actions para automatizar a construção e implantação do projeto Ansible. Inclui etapas para configurar os ambientes de execução, instalar dependências, propagar o projeto e implantar serviços Docker.

## Uso

1. Clone o repositório:

    ```bash
    git clone https://github.com/seuusuario/seu-repo.git
    cd seu-repo/ansible
    ```

2. Personalize o arquivo `inventory/hosts.ini` com suas variáveis de ambiente.

3. Defina a variável de ambiente `ANSIBLE_PROJECT`:

    ```bash
    export ANSIBLE_PROJECT=/caminho/para/seu/projeto/ansible
    ```

4. Execute os playbooks usando Ansible:

    ```bash
    ansible-playbook -i inventory/hosts.ini playbooks/setup_ansible_runtime.yml
    ansible-playbook -i inventory/hosts.ini playbooks/setup_ansible_dependencies.yml
    ansible-playbook -i inventory/hosts.ini playbooks/propagate_ansible_project.yml
    ansible-playbook -i inventory/hosts.ini playbooks/deploy-docker.yml
    ```

## Contribuindo

Contribuições são bem-vindas! Por favor, faça um fork do repositório e envie um pull request com suas alterações.

## Licença

Este projeto está licenciado sob a Licença MIT. Veja o arquivo [LICENSE](../LICENSE) para mais detalhes.
