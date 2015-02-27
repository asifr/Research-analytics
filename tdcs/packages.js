(function() {
  packages = {

	// Lazily construct the package hierarchy from class names.
	root: function(classes) {
	  var map = {};

	  function find(name, data) {
		var node = map[name], i;
		if (!node) {
		  node = map[name] = data || {name: name, children: []};
		  if (name.length) {
			// node.parent = find(name.substring(0, i = name.lastIndexOf(".")));
			node.parent = find(name.substring(0, i = name.lastIndexOf(".")));
			node.parent.children.push(node);
			// console.log(node.parent);
			node.key = name;
		  }
		}
		return node;
	  }

	  classes.forEach(function(d) {
		find(d.name, d);
	  });

	  return map[""];
	},

	// Return a list of collaborators for the given array of nodes.
	collaborators: function(nodes) {
	  var map = {},
		  collaborators = [];

	  // Compute a map from name to node.
	  nodes.forEach(function(d) {
		map[d.name] = d;
	  });

	  // For each import, construct a link from the source to target node.
	  nodes.forEach(function(d) {
		if (d.collaborators) d.collaborators.forEach(function(i) {
		  collaborators.push({source: map[d.name], target: map[i]});
		});
	  });

	  return collaborators;
	}

  };
})();
