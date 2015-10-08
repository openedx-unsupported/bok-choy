{
  "rules": [{
      "id": "fake-rule",
      "selector": "div",
      "enabled": true,
      "tags": [ "custom" ],
      "all": [],
      "any": [ "fake-rule" ],
      "none": [],
      "metadata": {
        "description": "This is a rule used for testing the bok choy integration.",
        "help": "When enabled, tests/site/accessibility.html should fail on this rule.",
        "helpUrl": "There isn't a help url for this!"
      }
  }],
  "checks": [{
    "id": "fake-rule",
    "metadata": {
      "impact": "critical",
      "messages": {
        "pass": function anonymous(it) {
          return "Message for when it passes";
        },
        "fail": function anonymous(it) {
          return "Message for when it fails";
        }
      }
    },
    evaluate: function(node, options) {
      return axe.commons.dom.isFocusable(document.getElementById("limit_scope"));
    },
    after: function(results, options) {return [ results[0] ];}
  }]
}
