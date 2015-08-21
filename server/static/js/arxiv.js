var subjects = {
    "all": [
        "Sub-domains"
    ],
    "Physics": [
        "Astrophysics",
        "Astrophysics - Astrophysics of Galaxies",
        "Astrophysics - Cosmology and Nongalactic Astrophysics",
        "Astrophysics - Earth and Planetary Astrophysics",
        "Astrophysics - High Energy Astrophysical Phenomena",
        "Astrophysics - Instrumentation and Methods for Astrophysics",
        "Astrophysics - Solar and Stellar Astrophysics",
        "Condensed Matter",
        "Condensed Matter - Disordered Systems and Neural Networks",
        "Condensed Matter - Materials Science",
        "Condensed Matter - Mesoscale and Nanoscale Physics",
        "Condensed Matter - Other Condensed Matter",
        "Condensed Matter - Quantum Gases",
        "Condensed Matter - Soft Condensed Matter",
        "Condensed Matter - Statistical Mechanics",
        "Condensed Matter - Strongly Correlated Electrons",
        "Condensed Matter - Superconductivity",
        "General Relativity and Quantum Cosmology",
        "High Energy Physics - Experiment",
        "High Energy Physics - Lattice",
        "High Energy Physics - Phenomenology",
        "High Energy Physics - Theory",
        "Mathematical Physics",
        "Nonlinear Sciences - Adaptation and Self-Organizing Systems",
        "Nonlinear Sciences - Cellular Automata and Lattice Gases",
        "Nonlinear Sciences - Chaotic Dynamics",
        "Nonlinear Sciences - Exactly Solvable and Integrable Systems",
        "Nonlinear Sciences - Pattern Formation and Solitons",
        "Nuclear Experiment",
        "Nuclear Theory",
        "Physics - Accelerator Physics",
        "Physics - Atmospheric and Oceanic Physics",
        "Physics - Atomic Physics",
        "Physics - Atomic and Molecular Clusters",
        "Physics - Biological Physics",
        "Physics - Chemical Physics",
        "Physics - Classical Physics",
        "Physics - Computational Physics",
        "Physics - Data Analysis, Statistics and Probability",
        "Physics - Fluid Dynamics",
        "Physics - General Physics",
        "Physics - Geophysics",
        "Physics - History and Philosophy of Physics",
        "Physics - Instrumentation and Detectors",
        "Physics - Medical Physics",
        "Physics - Optics",
        "Physics - Physics Education",
        "Physics - Physics and Society",
        "Physics - Plasma Physics",
        "Physics - Popular Physics",
        "Physics - Space Physics",
        "Quantum Physics"
    ],
    "Computer Science" : [
        "Computer Science - Artificial Intelligence",
        "Computer Science - Computation and Language",
        "Computer Science - Computational Complexity",
        "Computer Science - Computational Engineering, Finance, and Science",
        "Computer Science - Computational Geometry",
        "Computer Science - Computer Science and Game Theory",
        "Computer Science - Computer Vision and Pattern Recognition",
        "Computer Science - Computers and Society",
        "Computer Science - Cryptography and Security",
        "Computer Science - Data Structures and Algorithms",
        "Computer Science - Databases",
        "Computer Science - Digital Libraries",
        "Computer Science - Discrete Mathematics",
        "Computer Science - Distributed, Parallel, and Cluster Computing",
        "Computer Science - Emerging Technologies",
        "Computer Science - Formal Languages and Automata Theory",
        "Computer Science - Graphics",
        "Computer Science - Hardware Architecture",
        "Computer Science - Human-Computer Interaction",
        "Computer Science - Information Retrieval",
        "Computer Science - Information Theory",
        "Computer Science - Learning",
        "Computer Science - Logic in Computer Science",
        "Computer Science - Mathematical Software",
        "Computer Science - Multiagent Systems",
        "Computer Science - Multimedia",
        "Computer Science - Networking and Internet Architecture",
        "Computer Science - Neural and Evolutionary Computing",
        "Computer Science - Numerical Analysis",
        "Computer Science - Operating Systems",
        "Computer Science - Other Computer Science",
        "Computer Science - Performance",
        "Computer Science - Programming Languages",
        "Computer Science - Robotics",
        "Computer Science - Social and Information Networks",
        "Computer Science - Software Engineering",
        "Computer Science - Sound",
        "Computer Science - Symbolic Computation",
        "Computer Science - Systems and Control"
    ],
    "Mathematics" : [
        "Mathematics - Algebraic Geometry",
        "Mathematics - Algebraic Topology",
        "Mathematics - Analysis of PDEs",
        "Mathematics - Category Theory",
        "Mathematics - Classical Analysis and ODEs",
        "Mathematics - Combinatorics",
        "Mathematics - Commutative Algebra",
        "Mathematics - Complex Variables",
        "Mathematics - Differential Geometry",
        "Mathematics - Dynamical Systems",
        "Mathematics - Functional Analysis",
        "Mathematics - General Mathematics",
        "Mathematics - General Topology",
        "Mathematics - Geometric Topology",
        "Mathematics - Group Theory",
        "Mathematics - History and Overview",
        "Mathematics - K-Theory and Homology",
        "Mathematics - Logic",
        "Mathematics - Metric Geometry",
        "Mathematics - Number Theory",
        "Mathematics - Numerical Analysis",
        "Mathematics - Operator Algebras",
        "Mathematics - Optimization and Control",
        "Mathematics - Probability",
        "Mathematics - Quantum Algebra",
        "Mathematics - Representation Theory",
        "Mathematics - Rings and Algebras",
        "Mathematics - Spectral Theory",
        "Mathematics - Statistics Theory",
        "Mathematics - Symplectic Geometry"
    ],
    "Quantitative Biology": [
        "Quantitative Biology - Biomolecules",
        "Quantitative Biology - Cell Behavior",
        "Quantitative Biology - Genomics",
        "Quantitative Biology - Molecular Networks",
        "Quantitative Biology - Neurons and Cognition",
        "Quantitative Biology - Other Quantitative Biology",
        "Quantitative Biology - Populations and Evolution",
        "Quantitative Biology - Quantitative Methods",
        "Quantitative Biology - Subcellular Processes",
        "Quantitative Biology - Tissues and Organs"
    ],
    "Quantitative Finance" : [
        "Quantitative Finance - Computational Finance",
        "Quantitative Finance - General Finance",
        "Quantitative Finance - Portfolio Management",
        "Quantitative Finance - Pricing of Securities",
        "Quantitative Finance - Risk Management",
        "Quantitative Finance - Statistical Finance",
        "Quantitative Finance - Trading and Market Microstructure"
    ],
    "Statistics" : [
        "Statistics - Applications",
        "Statistics - Computation",
        "Statistics - Machine Learning",
        "Statistics - Methodology",
        "Statistics - Other Statistics"
    ]
}

function setSubdomain(domain) {
    var sublist = subjects[domain];
    var subselect = $("#subdomain");
    if (domain == "all") {
        subselect.prop("disabled", true);
    } else {
        subselect.prop("disabled", false);
    }
    subselect.html("");
    subselect.append('<option value="all">All subdomains</option>');
    for (var i = 0; i < sublist.length; i++) {
        var subdomain = sublist[i];
        subselect.append('<option value="' + subdomain + '">' + subdomain + '</option>');
    }
};


