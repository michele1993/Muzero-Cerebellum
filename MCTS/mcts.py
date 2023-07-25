class MCTS():
    """ Define class to run MCTS"""

    def __init__(
        self,
        discount,
        dirichlet_alpha,
        n_simulations,
        batch_s,
        lr,
        device,
        h_dim=64,
        clip_grad=True,
        root_exploration_eps = 0.25,
    ):

        self.discount = discount
        self.dirichlet_alpha = dirichlet_alpha
        self.root_exploration_eps = root_exploration_eps
        self.n_simulations = n_simulations
        self.batch_s = batch_s
        self.dev = device
            
    def run_mcts(state, network, temperature, deterministic=False):           
        """ Run MCT
        Args:
            state: current obs from the environment.
            network: MuZeron network instance
            tempreature: a parameter controls the level of exploration when generate policy action probabilities after MCTS search.
            deterministic: after the MCTS search, choose the child node with most visits number to play in the real environment,
         instead of sample through a probability distribution, default off.
         Returns:
            tuple contains:
            a integer indicate the sampled action to play in the environment.
            a 1D numpy.array search policy action probabilities from the MCTS search result.
            a float represent the search value of the root node.
        """

        # Create root node
        state = torch.from_numpy(state).to(self.dev)
        network_ouput = network.initial_inference(state)
        prior_prob = network_ouput.pi_probs
        root_node = Node(prior=0.0) # the root node does not have prior probs since it is the root

        # Add dirichlet noise to the prior probabilities to root node.
        if not deterministic and self.root_dirichlet_alpha > 0.0 and self.root_exploration_eps > 0.0:
            prior_prob = self.add_dirichlet_noise(prior_prob, eps=config.root_exploration_eps, alpha=config.root_dirichlet_alpha)
        
        # fill node with data and add "children actions", by expanding
        root_node.expand(prior_prob,network_ouput.h_state, network_ouput.rwd) 

        for _ in range(self.n_simulations):
            ## ====  Phase 1 - Select ====
            # Select best child node until reach a leaf
            node = root_node

            while node.is_expanded:
                node = node.best_child(self) # pass MCTS object to have access to the config

           ## ==== Phase 2 - Expand and evaluation ==== 
           h_state = torch.from_numpy(node.parent.h_state).to(self.dev)
           action = torch.tensor([node.move], device=self.dev)
           network_ouput = network.recurrent_inference(h_state, action)

           node.expand(prior_prob, network_ouput.h_state, network_ouput.rwd) # I don't understand prior prob here, shouldn't come from a network_output?

           ## ==== Phase 3 - Backup on leaf node ====
           node.backup(network_ouput.value, self)
        
        # Play: generate action prob from the root node to be played in the env.
        child_visits = root_node.child_N

        pi_prob = self.generate_play_policy(child_visits, temperature)

    def add_dirichlet_noise(prob, eps=0.25, alpha=0.25):
        """Add dirichlet noise to a given probabilities.
        Args:
            prob: a numpy.array contains action probabilities we want to add noise to.
            eps: epsilon constant to weight the priors vs. dirichlet noise.
            alpha: parameter of the dirichlet noise distribution.

        Returns:
            action probabilities with added dirichlet noise.
        """    

        alphas = np.ones_like(prob) * alpha
        noise = np.random.dirichlet(alphas)
        noised_prob = (1 - eps) * prob + eps * noise

        return noised_prob
                    
    def generate_play_policy(visits_count, temperature):
        """ Returns policy action probabilities proportional to their exponentiated visit count during MCTS 
        Args:
            visits_count: a 1D numpy.array contains child node visits count.
            temperature: a parameter controls the level of exploration.
        Returns:        
            a 1D numpy.array contating the action prob for real env
        """

        if not 0.0 <= temperature <= 1.0:
            raise ValueError(f"Expect `temperature` to be in the range [0.0, 1.0], got {temperature}")

        visits_count = np.asarray(visits_count)

        if temperature > 0.0:
            # limit the exponent in the range of [1.0, 5.0]
            # to avoid overflow when doing power operation over large numbers
            exp = max(1.0,min(5.0, 1.0/temperature))
            visits_count = np.power(visits_count,exp)

        return visits_count / np.sum(visits_count)
        
