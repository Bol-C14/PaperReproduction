def corrected(self, graph, cov):
    pred_prob = torch.zeros_like(graph.prob, device=graph.prob.device)
    pred_prob[graph.forward_level == 0] = graph.prob[graph.forward_level == 0]
    max_level = torch.max(graph.forward_level) + 1
    for level in range(1, max_level):
        level_nodes = graph.forward_index[graph.forward_level == level]
        if level_nodes.size(0) == 0:
            continue
        level_mask = graph.forward_level[graph.edge_index[1]] == level
        edge_index = graph.edge_index[:, level_mask]
        unique_targets, _, cop_result = self._cop(edge_index, pred_prob, graph.x)
        pred_prob[unique_targets] = cop_result + cov[unique_targets].squeeze(1)
    return pred_prob
