from kubernetes import client, config

def namespace_health(environment: str, context: str, namespace: str):
    try:
        config.load_kube_config(context=context)
        core = client.CoreV1Api()
        apps = client.AppsV1Api()
        batch = client.BatchV1Api()
        autoscaling = client.AutoscalingV2Api()
        policy = client.PolicyV1Api()

        pods = core.list_namespaced_pod(namespace).items
        deps = apps.list_namespaced_deployment(namespace).items
        sts = apps.list_namespaced_stateful_set(namespace).items
        jobs = batch.list_namespaced_job(namespace).items
        pvcs = core.list_namespaced_persistent_volume_claim(namespace).items
        hpas = autoscaling.list_namespaced_horizontal_pod_autoscaler(namespace).items
        pdbs = policy.list_namespaced_pod_disruption_budget(namespace).items
        events = core.list_namespaced_event(namespace).items

        out = {
            'environment': environment,
            'namespace': namespace,
            'state': 'healthy',
            'deployments': [],
            'statefulsets': [],
            'pods': [],
            'jobs': [],
            'pvcs': [],
            'hpas': [],
            'pdbs': [],
            'warnings': [],
        }

        def degrade():
            out['state'] = 'degraded'

        for d in deps:
            desired = d.spec.replicas or 0
            ready = d.status.ready_replicas or 0
            state = 'healthy' if desired == ready else 'degraded'
            if state != 'healthy': degrade()
            out['deployments'].append({'name': d.metadata.name, 'ready': ready, 'desired': desired, 'state': state})

        for s in sts:
            desired = s.spec.replicas or 0
            ready = s.status.ready_replicas or 0
            state = 'healthy' if desired == ready else 'degraded'
            if state != 'healthy': degrade()
            out['statefulsets'].append({'name': s.metadata.name, 'ready': ready, 'desired': desired, 'state': state})

        for p in pods:
            restarts = sum((c.restart_count or 0) for c in (p.status.container_statuses or []))
            waiting = [c.state.waiting.reason for c in (p.status.container_statuses or []) if c.state and c.state.waiting and c.state.waiting.reason]
            state = 'healthy' if p.status.phase in ('Running', 'Succeeded') and not waiting else 'degraded'
            if state != 'healthy': degrade()
            elif restarts >= 5:
                state = 'warning'
            out['pods'].append({'name': p.metadata.name, 'phase': p.status.phase, 'restarts': restarts, 'waiting': waiting, 'state': state})

        for j in jobs:
            failed = j.status.failed or 0
            active = j.status.active or 0
            succeeded = j.status.succeeded or 0
            state = 'degraded' if failed else 'healthy'
            if failed: degrade()
            out['jobs'].append({'name': j.metadata.name, 'failed': failed, 'active': active, 'succeeded': succeeded, 'state': state})

        for pvc in pvcs:
            phase = pvc.status.phase or 'Unknown'
            state = 'healthy' if phase == 'Bound' else 'degraded'
            if state != 'healthy': degrade()
            out['pvcs'].append({'name': pvc.metadata.name, 'phase': phase, 'state': state})

        for hpa in hpas:
            out['hpas'].append({'name': hpa.metadata.name, 'current_replicas': hpa.status.current_replicas, 'desired_replicas': hpa.status.desired_replicas})

        for pdb in pdbs:
            disruptions = pdb.status.disruptions_allowed if pdb.status else None
            state = 'warning' if disruptions == 0 else 'healthy'
            out['pdbs'].append({'name': pdb.metadata.name, 'disruptions_allowed': disruptions, 'state': state})

        warning_events = [e for e in events if getattr(e, 'type', None) == 'Warning']
        warning_events.sort(key=lambda e: getattr(e, 'last_timestamp', None) or getattr(e.metadata, 'creation_timestamp', None), reverse=True)
        out['warnings'] = [
            {'reason': e.reason, 'message': e.message, 'object': f"{e.involved_object.kind}/{e.involved_object.name}"}
            for e in warning_events[:20]
        ]
        return out
    except Exception as exc:
        return {'environment': environment, 'namespace': namespace, 'state': 'unknown', 'error': str(exc)}
