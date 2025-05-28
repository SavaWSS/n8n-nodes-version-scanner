const DEBUG = false;

const extractNodeName = (typeField) => {
    if (typeField && typeField.includes('n8n-nodes-base.')) {
        return typeField.split('n8n-nodes-base.')[1];
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

    // Извлекаем данные из структуры n8n
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
    let html = '';

    for (const [workflowName, nodes] of Object.entries(workflowResults)) {
        // Получаем ID воркфлоу из первого узла
        const workflowId = nodes[0]?.workflow_id || '';
        const workflowUrl = workflowId ? `https://ynn.2bv.ru/workflow/${workflowId}` : '#';
        
        // Добавляем заголовок воркфлоу со ссылкой
        html += `<h2 style="margin: 20px 0 10px 0;">`;
        html += `<a href="${workflowUrl}" style="text-decoration: none; color: #333;" target="_blank">${workflowName}</a>`;
        html += `</h2>`;
        
        // Создаем таблицу для текущего воркфлоу
        html += '<table style="border-collapse: collapse; width: 100%; margin-bottom: 30px;">';
        html += '<thead><tr style="background-color: #f5f5f5;">';
        html += '<th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Нода</th>';
        html += '<th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Текущая версия</th>';
        html += '<th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Последняя версия</th>';
        html += '<th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Статус</th>';
        html += '</tr></thead><tbody>';

        nodes.forEach((node) => {
            const isOutdated = node.match && node.current_version < node.latest_version;
            const rowStyle = isOutdated ? 'background-color: #fff3f3;' : '';
            
            html += `<tr style="${rowStyle}">`;
            html += `<td style="border: 1px solid #ddd; padding: 8px;">${node.node_name}</td>`;
            html += `<td style="border: 1px solid #ddd; padding: 8px;">${node.current_version}</td>`;
            html += `<td style="border: 1px solid #ddd; padding: 8px;">${node.latest_version}</td>`;
            html += `<td style="border: 1px solid #ddd; padding: 8px;">${node.match ? (isOutdated ? '⚠️ Устарела' : '✅ Актуальна') : '❓ Не найдена'}</td>`;
            html += '</tr>';
        });

        html += '</tbody></table>';
    }

    return html;
};

const main = () => {
    try {
        const nodesInUse = $('nodes-in-use').all();
        const nodeVersions = $('node_versions').all();

        if (DEBUG) {
            console.log('Входные данные получены:');
            console.log('nodesInUse:', nodesInUse);
            console.log('nodeVersions:', nodeVersions);
        }

        if (!nodesInUse || !nodeVersions) {
            return {
                html: '<div style="color: red;">Отсутствуют необходимые данные для анализа</div>'
            };
        }

        const results = analyzeWorkflows(nodesInUse, nodeVersions);
        if (DEBUG) {
            console.log('Результаты анализа:', results);
        }

        // Группировка результатов по имени воркфлоу
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
            html: `<div style="color: red;">Критическая ошибка: ${error.message}</div>`
        };
    }
};

return main(); 