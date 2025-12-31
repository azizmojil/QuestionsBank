(() => {
    const versionSelect = document.getElementById('survey-version-select');
    const questionsList = document.getElementById('questions-list');
    const canvas = document.getElementById('canvas');
    const connectionsLayer = document.getElementById('connections-layer');
    const flowContainer = document.getElementById('flow-container');
    const saveButton = document.getElementById('save-flow');
    const localeEl = document.getElementById('routing-locale');

    const locale = localeEl ? JSON.parse(localeEl.textContent) : {};
    const dataUrl = flowContainer?.dataset.dataUrl;
    const saveUrl = flowContainer?.dataset.saveUrl;

    const state = {
        nodes: new Map(), // questionId -> HTMLElement
        connections: [],  // { sourceId, targetId, condition, priority, path }
        layout: {},
    };

    let activeConnection = null;

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i += 1) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === `${name}=`) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function resetCanvas() {
        state.nodes.clear();
        state.connections.forEach((conn) => conn.path?.remove());
        state.connections = [];
        state.layout = {};
        canvas.innerHTML = '';
        connectionsLayer.innerHTML = '';
    }

    function defaultPosition(index) {
        const colWidth = 260;
        const rowHeight = 150;
        const col = index % 3;
        const row = Math.floor(index / 3);
        return { x: 40 + (col * colWidth), y: 30 + (row * rowHeight) };
    }

    function serializeLayout() {
        const layout = {};
        state.nodes.forEach((node, id) => {
            layout[id] = {
                x: Math.round(parseFloat(node.style.left) || 0),
                y: Math.round(parseFloat(node.style.top) || 0),
                label: node.dataset.label,
            };
        });
        return layout;
    }

    function removeConnectionsForNode(questionId) {
        state.connections = state.connections.filter((conn) => {
            const shouldRemove = conn.sourceId === questionId || conn.targetId === questionId;
            if (shouldRemove && conn.path) {
                conn.path.remove();
            }
            return !shouldRemove;
        });
        updateConnections();
    }

    function removeConnection(connection) {
        if (connection.path) {
            connection.path.remove();
        }
        state.connections = state.connections.filter((c) => c !== connection);
        updateConnections();
    }

    function updateConnections() {
        state.connections.forEach((conn) => {
            const sourceNode = state.nodes.get(String(conn.sourceId));
            const targetNode = state.nodes.get(String(conn.targetId));
            if (!sourceNode || !targetNode || !conn.path) {
                return;
            }
            const srcRect = sourceNode.getBoundingClientRect();
            const tgtRect = targetNode.getBoundingClientRect();
            const canvasRect = canvas.getBoundingClientRect();

            const x1 = srcRect.left + (srcRect.width / 2) - canvasRect.left;
            const y1 = srcRect.bottom - canvasRect.top;
            const x2 = tgtRect.left + (tgtRect.width / 2) - canvasRect.left;
            const y2 = tgtRect.top - canvasRect.top;

            const d = `M ${x1} ${y1} C ${x1} ${y1 + 50}, ${x2} ${y2 - 50}, ${x2} ${y2}`;
            conn.path.setAttribute('d', d);
        });
    }

    function drawConnection(connection) {
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.classList.add('connection-line');
        path.addEventListener('click', () => {
            const message = locale.deleteConnection || 'Remove this connection?';
            if (window.confirm(message)) {
                removeConnection(connection);
            }
        });
        connectionsLayer.appendChild(path);
        connection.path = path;
        state.connections.push(connection);
        updateConnections();
    }

    function extractSourceFromCondition(condition) {
        if (!condition || typeof condition !== 'object') return null;
        if (condition.fallback) return null;
        const condList = Array.isArray(condition.conditions) ? condition.conditions : [];
        const match = condList.find((c) => c && c.question);
        return match ? match.question : null;
    }

    function buildCondition(sourceId) {
        const isFallback = window.confirm(locale.fallbackPrompt || 'Use fallback (no conditions)?');
        if (isFallback) {
            return { fallback: true };
        }
        const operator = window.prompt(locale.operatorPrompt || 'Enter comparison operator (==, !=, >, <, in, contains):', '==');
        if (operator === null || operator.trim() === '') {
            return null;
        }
        const value = window.prompt(locale.valuePrompt || 'Enter comparison value:');
        if (value === null) {
            return null;
        }
        return {
            conditions: [
                {
                    question: sourceId,
                    operator: operator.trim(),
                    value: value,
                },
            ],
        };
    }

    function finalizeConnection(sourceId, targetId) {
        if (sourceId === targetId) return;
        const duplicate = state.connections.some(
            (c) => c.sourceId === sourceId && c.targetId === targetId,
        );
        if (duplicate) {
            if (locale.duplicateConnection) {
                window.alert(locale.duplicateConnection);
            }
            return;
        }

        const condition = buildCondition(sourceId);
        if (!condition) return;

        const connection = {
            sourceId,
            targetId,
            condition,
            priority: state.connections.length,
            path: null,
        };
        drawConnection(connection);
    }

    function attachDrag(node, questionId) {
        let isDragging = false;
        let startX = 0;
        let startY = 0;

        node.addEventListener('mousedown', (e) => {
            if (e.target.closest('.connection-point')) {
                return;
            }
            isDragging = true;
            startX = e.clientX - node.offsetLeft;
            startY = e.clientY - node.offsetTop;
            node.style.zIndex = 100;
        });

        window.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            const newX = e.clientX - startX;
            const newY = e.clientY - startY;
            node.style.left = `${newX}px`;
            node.style.top = `${newY}px`;
            updateConnections();
        });

        window.addEventListener('mouseup', () => {
            if (isDragging) {
                state.layout[String(questionId)] = {
                    x: parseFloat(node.style.left) || 0,
                    y: parseFloat(node.style.top) || 0,
                    label: node.dataset.label,
                };
            }
            isDragging = false;
            node.style.zIndex = 10;
        });
    }

    function ensureNode(question, position) {
        const existing = state.nodes.get(String(question.id));
        if (existing) {
            return existing;
        }

        const node = document.createElement('div');
        node.className = 'flow-node';
        node.dataset.id = question.id;
        node.dataset.label = question.label || `${locale.questionLabel || 'Question'} ${question.id}`;

        const nodePosition = position || defaultPosition(state.nodes.size);
        node.style.left = `${nodePosition.x}px`;
        node.style.top = `${nodePosition.y}px`;

        const header = document.createElement('div');
        header.className = 'flow-node-header';
        const title = document.createElement('span');
        title.textContent = question.code || `Q${question.id}`;
        const closeBtn = document.createElement('button');
        closeBtn.type = 'button';
        closeBtn.className = 'btn-close';
        closeBtn.setAttribute('aria-label', 'remove');
        closeBtn.innerHTML = '&times;';
        closeBtn.addEventListener('click', () => {
            const message = locale.removeNode || 'Remove this node and its connections?';
            if (window.confirm(message)) {
                removeConnectionsForNode(question.id);
                state.nodes.delete(String(question.id));
                node.remove();
            }
        });
        header.append(title, closeBtn);

        const body = document.createElement('div');
        body.className = 'flow-node-body';
        body.textContent = question.label || `${locale.questionLabel || 'Question'} ${question.id}`;

        const inPoint = document.createElement('div');
        inPoint.className = 'connection-point point-in';
        inPoint.title = 'Input';
        inPoint.addEventListener('mouseup', (e) => {
            e.stopPropagation();
            if (activeConnection) {
                finalizeConnection(activeConnection.sourceId, question.id);
                activeConnection = null;
            }
        });

        const outPoint = document.createElement('div');
        outPoint.className = 'connection-point point-out';
        outPoint.title = 'Output';
        outPoint.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            activeConnection = { sourceId: question.id };
        });

        node.append(header, body, inPoint, outPoint);
        canvas.appendChild(node);
        state.nodes.set(String(question.id), node);
        attachDrag(node, question.id);
        return node;
    }

    function renderSidebar(questions) {
        questionsList.innerHTML = '';
        if (!questions.length) {
            const empty = document.createElement('div');
            empty.className = 'muted text-center empty-hint';
            empty.textContent = locale.selectVersion || 'Select a version to load questions.';
            questionsList.appendChild(empty);
            return;
        }

        questions.forEach((q) => {
            const el = document.createElement('div');
            el.className = 'draggable-item';
            el.draggable = true;
            el.textContent = q.label || `${locale.questionLabel || 'Question'} ${q.id}`;
            el.dataset.id = q.id;

            el.addEventListener('dragstart', (ev) => {
                ev.dataTransfer.setData('text/plain', JSON.stringify(q));
            });

            questionsList.appendChild(el);
        });
    }

    function addConnectionFromRule(rule) {
        const sourceId = extractSourceFromCondition(rule.condition);
        if (!sourceId) {
            return;
        }
        const connection = {
            sourceId,
            targetId: rule.to_question,
            condition: rule.condition || {},
            priority: rule.priority,
            path: null,
        };
        drawConnection(connection);
    }

    function loadVersion(versionId) {
        resetCanvas();
        if (!versionId || !dataUrl) {
            renderSidebar([]);
            return;
        }

        fetch(`${dataUrl}?version_id=${encodeURIComponent(versionId)}`)
            .then((resp) => {
                if (!resp.ok) {
                    throw new Error('Failed to load routing data');
                }
                return resp.json();
            })
            .then((data) => {
                state.layout = data.layout || {};
                renderSidebar(data.questions || []);
                (data.questions || []).forEach((q, idx) => {
                    const layoutPos = state.layout[String(q.id)];
                    ensureNode(q, layoutPos || defaultPosition(idx));
                });
                (data.rules || []).forEach(addConnectionFromRule);
                updateConnections();
            })
            .catch((err) => {
                console.error(err);
            });
    }

    function handleDrop(e) {
        e.preventDefault();
        const payload = e.dataTransfer.getData('text/plain');
        if (!payload) return;
        let question;
        try {
            question = JSON.parse(payload);
        } catch (ex) {
            return;
        }
        const rect = canvas.getBoundingClientRect();
        ensureNode(question, {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top,
        });
        updateConnections();
    }

    function saveRouting() {
        const versionId = versionSelect?.value;
        if (!versionId) {
            window.alert(locale.missingVersion || 'Please choose a version first.');
            return;
        }
        if (!saveUrl) return;

        const payload = {
            version_id: versionId,
            layout: serializeLayout(),
            rules: state.connections.map((conn, idx) => ({
                to_question: conn.targetId,
                condition: conn.condition,
                priority: typeof conn.priority === 'number' ? conn.priority : idx,
                description: conn.description || '',
            })),
        };

        fetch(saveUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify(payload),
        })
            .then((resp) => {
                if (!resp.ok) {
                    return resp.json().then((data) => {
                        throw new Error(data.message || 'Save failed');
                    });
                }
                return resp.json();
            })
            .then(() => {
                window.alert(locale.saveSuccess || 'Routing saved.');
            })
            .catch((err) => {
                console.error(err);
                window.alert(locale.saveError || 'Unable to save routing.');
            });
    }

    if (canvas) {
        canvas.addEventListener('dragover', (e) => e.preventDefault());
        canvas.addEventListener('drop', handleDrop);
    }

    versionSelect?.addEventListener('change', (e) => {
        loadVersion(e.target.value);
    });

    saveButton?.addEventListener('click', saveRouting);

    loadVersion(versionSelect?.value);
})();
