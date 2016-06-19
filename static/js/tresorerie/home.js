var trees = [];

function show(tree) {
    $('#pricing').html(
            '<h3>' + tree['question'] + '</h3>'
    );

    $.each(tree['children'], function(index, child) {
        $('#pricing').append(
            '<label class="radio-inline">' + 
                '<input class="selector" type="radio" name=' + tree['option'] + ' index=' + index + '>' + child['option'] + 
            '</label>'
        );
        trees.push(child);
        $('input[name=' + tree['option'] + '][index=' + index + ']').attr('tree', Object.keys(trees).length - 1);
    });
};

$(function () {
    const OPTIONS = [
        {'option': 'first', 'question': gettext('Quelle est votre formation ?'), 'children': [
            {'option': 'Autre', 'price': '1100'},

            {'option': 'FIP', 'question': gettext('Voulez-vous payer en plusieurs fois ?'), 'children': [
                {'option': 'Oui', 'price': '1767'},
                {'option': 'Non', 'price': '5100'}
            ]},

            {'option': 'FIG', 'question': gettext('En quelle année êtes-vous ?'), 'children': [
                {'option': '1A', 'question': gettext('Souhaitez-vous payer en 3 fois ?'), 'children': [
                    {'option': 'Oui', 'price': '2940'},
                    {'option': 'Non', 'price': '8600'}
                ]},

                {'option': '2A', 'question': gettext('Combien de temps restez-vous sur le campus ?'), 'children': [
                    {'option': '6 mois', 'question': gettext('Souhaitez-vous payer en 3 fois ?'), 'children': [
                        {'option': 'Oui', 'price': '1767'},
                        {'option': 'Non', 'price': '5100'}
                    ]},

                    {'option': '1 an', 'question': gettext('Souhaitez-vous payer en 3 fois ?'), 'children': [
                        {'option': 'Oui', 'price': '2940'},
                        {'option': 'Non', 'price': '8600'}
                    ]}
                ]},

                {'option': '3A', 'question': gettext('Souhaitez-vous payer en 3 fois ?'), 'children': [
                    {'option': 'Oui', 'price': '1767'},
                    {'option': 'Non', 'price': '5100'}
                ]}
            ]}
        ]}
    ];

    show(OPTIONS[0]);

    $('#pricing').on('click', '.selector', function () {
        var tree = trees[parseInt($(this).attr('tree'))];

        if ('children' in tree) {
            show(tree);
        } else {
            $('#stripe').html(
                '<br> \
                <script \
                    src="https://checkout.stripe.com/checkout.js" class="stripe-button" \
                    data-key="pk_test_KE9qQquz3hhdRI54CcfBaukl" \
                    data-amount="' + tree['price'] + '" \
                    data-name="Association ResEl" \
                    data-description="Widget" \
                    data-image="/static/images/tresorerie/marketplace.png" \
                    data-locale="auto" \
                    data-zip-code="true" \
                    data-currency="eur"> \
                </script>'
            );
        }
    });
});