const DEBUG = false;

const NODE_ALIASES = {
    'n8n-nodes-base.respondToWebhook': 'respondWith',
    'n8n-nodes-base.html': 'extractionValues',
    '@n8n/n8n-nodes-langchain.chatTrigger': 'allowFileUploads',
    'n8n-nodes-base.wait': 'amount'
};

const extractNodeName = (typeField) => {
    if (!typeField) return typeField;
    
    // Проверяем наличие элиаса
    if (typeField in NODE_ALIASES) {
        return NODE_ALIASES[typeField];
    }
    
    // Стандартная обработка для n8n-nodes-base
    if (typeField.includes('.')) {
        return typeField.split('.')[1];
    }
    
    return typeField;
};

const compareVersions = (currentVersion, latestVersion) => {
    return currentVersion < latestVersion;
};

const getVersionInfo = (nodeData) => {
    try {
        const versionInfo = nodeData.version_info || {};
        return versionInfo.latest_version || 0.0;
    } catch (error) {
        return 0.0;
    }
};

const analyzeWorkflows = (nodesInUse, nodeVersions) => {
    const outdatedNodes = [];
    const unmatchedNodes = [];

    if (DEBUG) {
        console.log('nodesInUse:', JSON.stringify(nodesInUse));
        console.log('nodeVersions:', JSON.stringify(nodeVersions));
    }

    if (!Array.isArray(nodesInUse)) {
        if (DEBUG) console.log('nodesInUse не является массивом');
        return [];
    }

    const workflows = nodesInUse.map(item => item.json);
    const versions = nodeVersions[0]?.json || {};

    if (DEBUG) {
        console.log('Обработанные воркфлоу:', workflows);
        console.log('Обработанные версии:', versions);
    }

    for (const workflow of workflows) {
        const workflowName = workflow.name || 'Unknown Workflow';
        const workflowId = workflow.id || '';
        const nodes = workflow.nodes || [];

        if (DEBUG) {
            console.log(`Обработка воркфлоу: ${workflowName}, количество нод: ${nodes.length}`);
        }

        for (const node of nodes) {
            try {
                const nodeTypeFull = node.type || '';
                const nodeType = extractNodeName(nodeTypeFull);
                const currentVersion = parseFloat(node.typeVersion) || 0.0;
                const nodeName = node.name || 'Unknown Node';

                if (DEBUG) {
                    console.log(`Обработка ноды: ${nodeType}, версия: ${currentVersion}`);
                }

                if (nodeType in versions) {
                    const latestVersion = getVersionInfo(versions[nodeType]);
                    if (DEBUG) {
                        console.log(`Найдена последняя версия: ${latestVersion}`);
                    }

                    if (compareVersions(currentVersion, latestVersion)) {
                        outdatedNodes.push({
                            workflow_name: workflowName,
                            workflow_id: workflowId,
                            node_type: nodeType,
                            current_version: currentVersion,
                            latest_version: latestVersion,
                            node_name: nodeName,
                            match: true
                        });
                    }
                } else {
                    unmatchedNodes.push({
                        workflow_name: workflowName,
                        workflow_id: workflowId,
                        node_type: nodeTypeFull,
                        current_version: 0.0,
                        latest_version: 0.0,
                        node_name: nodeName,
                        match: false
                    });
                }
            } catch (error) {
                if (DEBUG) {
                    console.log(`Ошибка при обработке ноды: ${error.message}`);
                }
                continue;
            }
        }
    }

    if (DEBUG) {
        console.log(`Найдено устаревших нод: ${outdatedNodes.length}`);
        console.log(`Найдено несоответствующих нод: ${unmatchedNodes.length}`);
    }

    return [...outdatedNodes, ...unmatchedNodes];
};

const generateHtmlTable = (workflowResults) => {
    let html = '<div class="container-fluid">';

    for (const [workflowName, nodes] of Object.entries(workflowResults)) {
        const workflowId = nodes[0]?.workflow_id || '';
        const workflowUrl = workflowId ? `https://ynn.2bv.ru/workflow/${workflowId}` : '#';
        
        html += `<div class="card mb-4">`;
        html += `<div class="card-header bg-light">`;
        html += `<h2 class="h5 mb-0">`;
        html += `<a href="${workflowUrl}" class="link-dark link-offset-2 link-underline-opacity-25 link-underline-opacity-100-hover" target="_blank">${workflowName}</a>`;
        html += `</h2>`;
        html += `</div>`;
        
        html += `<div class="card-body p-0">`;
        html += `<div class="table-responsive">`;
        html += `<table class="table table-hover table-striped mb-0">`;
        html += `<thead class="table-light">`;
        html += `<tr>`;
        html += `<th scope="col" style="width: 30%">Нода</th>`;
        html += `<th scope="col" style="width: 30%">Нода type</th>`;
        html += `<th scope="col" style="width: 10%">Текущая версия</th>`;
        html += `<th scope="col" style="width: 10%">Последняя версия</th>`;
        html += `<th scope="col" style="width: 20%">Статус</th>`;
        html += `</tr>`;
        html += `</thead>`;
        html += `<tbody>`;

        nodes.forEach((node) => {
            const isOutdated = node.match && node.current_version < node.latest_version;
            const rowClass = isOutdated ? 'table-danger' : '';
            
            // html += `<tr class="${rowClass}">`;
            html += `<tr>`;
            html += `<td>${node.node_name}</td>`;
            html += `<td>${node.node_type}</td>`;
            html += `<td>${node.current_version}</td>`;
            html += `<td>${node.latest_version}</td>`;
            html += `<td>`;
            if (node.match) {
                html += isOutdated 
                    ? '<span class="badge bg-warning text-dark">⚠️ Устарела</span>'
                    : '<span class="badge bg-success">✅ Актуальна</span>';
            } else {
                html += '<span class="badge bg-secondary">❓ Не найдена</span>';
            }
            html += `</td>`;
            html += `</tr>`;
        });

        html += `</tbody>`;
        html += `</table>`;
        html += `</div>`;
        html += `</div>`;
        html += `</div>`;
    }

    html += '</div>';
    return html;
};

const main = () => {
    try {
        const nodesInUse = $('Merge').all();
        const nodeVersions = $('node_versions').all();

        if (DEBUG) {
            console.log('Входные данные получены:');
            console.log('nodesInUse:', nodesInUse);
            console.log('nodeVersions:', nodeVersions);
        }

        if (!nodesInUse || !nodeVersions) {
            return {
                html: '<div class="alert alert-danger">Отсутствуют необходимые данные для анализа</div>'
            };
        }

        const results = analyzeWorkflows(nodesInUse, nodeVersions);
        if (DEBUG) {
            console.log('Результаты анализа:', results);
        }

        const workflowResults = {};
        for (const node of results) {
            if (!workflowResults[node.workflow_name]) {
                workflowResults[node.workflow_name] = [];
            }
            workflowResults[node.workflow_name].push(node);
        }

        if (DEBUG) {
            console.log('Финальные результаты:', workflowResults);
        }

        const htmlTable = generateHtmlTable(workflowResults);

        return {
            html: htmlTable
        };
    } catch (error) {
        if (DEBUG) {
            console.log('Критическая ошибка:', error);
        }
        return {
            html: `<div class="alert alert-danger">Критическая ошибка: ${error.message}</div>`
        };
    }
};

return main(); 