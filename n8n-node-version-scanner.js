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
                json: {
                    error: 'Отсутствуют необходимые данные для анализа'
                }
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

        return {
            json: workflowResults
        };
    } catch (error) {
        if (DEBUG) {
            console.log('Критическая ошибка:', error);
        }
        return {
            json: {
                error: `Критическая ошибка: ${error.message}`
            }
        };
    }
};

return main(); 