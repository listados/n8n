# Correções aplicadas no setup n8n

## 1. Porta não acessível no host
**Erro:** `ERR_CONNECTION_REFUSED` ao acessar `localhost:5678`  
**Causa:** `ports: - "5678"` só expõe entre containers, não mapeia pro host.  
**Fix:** `ports: - "5678:5678"`

---

## 2. Python não encontrado
**Erro:** `Python runner unavailable: Python 3 is missing from this system`  
**Causa:** `docker-compose.yml` usava `image: n8nio/n8n:latest`, ignorando o `Dockerfile` customizado.  
**Fix:** Substituir `image:` por `build: .`

---

## 3. Virtual environment ausente
**Erro:** `Python runner unavailable: Virtual environment is missing from this system`  
**Causa:** n8n espera o pacote `@n8n/task-runner-python` com um `.venv` em `/usr/local/lib/node_modules/@n8n/task-runner-python/.venv/bin/python`. 
Nada disso existia no container.  
**Fix:** Reescrever o `Dockerfile` com dois estágios:
- Estágio 1 (`python:3.13-alpine`): sparse-clone do source `packages/@n8n/task-runner-python` do repositório n8n na tag correta, 
criação do venv e instalação do pacote.
- Estágio 2: copiar Python 3.13, stdlib, `.so` e o diretório completo do task-runner para os paths que o n8n resolve em runtime.

> **Obs:** Alpine 3.22 só tem Python 3.12, mas o task-runner exige `>=3.13`. Usar `python:3.13-alpine` como builder resolve isso.

---

## 4. Violação de segurança (imports bloqueados)
**Erro:** `Security violations detected`  
**Causa:** Por padrão `N8N_RUNNERS_STDLIB_ALLOW` e `N8N_RUNNERS_EXTERNAL_ALLOW` são vazios, bloqueando qualquer `import`.  
**Fix:** Adicionar no `docker-compose.yml`:
```yaml
N8N_RUNNERS_STDLIB_ALLOW: "*"
N8N_RUNNERS_EXTERNAL_ALLOW: "*"
```

---

## 5. API do Python incompatível com n8n
**Erro:** `name '_input' is not defined` / `'list' object has no attribute 'first'`  
**Causa:** O código usava sintaxe JavaScript-style (`_input`, `_items.first()`, `item.json.campo`).  
**Fix:** No Python do n8n, as variáveis injetadas são:

| Modo | Variável | Tipo |
|---|---|---|
| Run once for all items | `_items` | `list` |
| Run once for each item | `_item` | `dict` |

```python
# Correto
input_item = _items[0]
xml_content = input_item["json"].get("data")
```
