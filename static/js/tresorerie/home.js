var trees;

function main(formation, member) {
    var tree;
    trees = [];

    $('.choices').removeClass('hidden');
    $('.stripe').addClass('hidden');

    if (member === 'false') {
        if (!formation.toLowerCase().includes('fip')) {
            tree = [
                {'name': 'choice', 'question': gettext("Que souhaitez-vous payer ?"), 'children': [
                    {'option': gettext("Adhésion seule - 1 €"), 'price': '100'},

                    {'name': 'duration', 'option': gettext("Pack tout compris (adhésion + accès Internet)"), 'question': gettext("Combien de temps restez-vous sur le campus ?"), 'children': [
                        {'option': gettext("1 mois - 11 €"), 'price': '1100'},

                        {'name': '3x6m', 'option': gettext("6 mois - 51 €"), 'question': gettext("Souhaitez-vous payer en 3 fois ?"), 'children': [
                            {'option': gettext("Oui - 17,70 € puis 16,70 € par mois"), 'price': '1770'},

                            {'option': gettext("Non - 51 €"), 'price': '5100'}
                        ]},

                        {'name': '3x1a', 'option': gettext("1 an - 86 €"), 'question': gettext("Souhaitez-vous payer en 3 fois ?"), 'children': [
                            {'option': gettext("Oui - 29,40 € puis 28,40 €"), 'price': '2940'},

                            {'option': gettext("Non - 86 €"), 'price': '8600'}
                        ]}
                    ]}
                ]}
            ]; 
        } else {
            tree = [
                {'name': 'choice', 'question': gettext("Que souhaitez-vous payer ?"), 'children': [
                    {'option': gettext("Adhésion seule - 1 €"), 'price': '100'},

                    {'name': '3x6m', 'option': gettext("Pack tout compris (adhésion + accès Internet) - 51 €"), 'question': gettext("Souhaitez-vous payer en 3 fois ?"), 'children': [
                        {'option': gettext("Oui - 17,70 € puis 16,70 € par mois"), 'price': '1770'},

                        {'option': gettext("Non - 51 €"), 'price': '5100'} 
                    ]}
                ]}
            ];
        };  
    } else {
        if (!formation.toLowerCase().includes('fip')) {
            tree = [
                {'name': 'choice', 'question': gettext("Combien de temps restez-vous sur le campus ?"), 'children': [
                    {'option': gettext("1 mois - 10 €"), 'price': '1000'},

                    {'name': '3x6m', 'option': gettext("6 mois - 50 €"), 'question': gettext("Souhaitez-vous payer en 3 fois ?"), 'children': [
                        {'option': gettext("Oui - 16,70 € par mois"), 'price': '1670'},

                        {'option': gettext("Non - 50 €"), 'price': '5000'}
                    ]},

                    {'name': '3x1a', 'option': gettext("1 an - 85 €"), 'question': gettext("Souhaitez-vous payer en 3 fois ?"), 'children': [
                        {'option': gettext("Oui - 28,40 €"), 'price': '2840'},

                        {'option': gettext("Non - 85 €"), 'price': '8500'}
                    ]}
                ]}
            ];
        } else {
            tree = [
                {'name': 'choice', 'question': gettext("Souhaitez-vous payer en 3 fois ?"), 'children': [
                    {'option': gettext("Oui - 16,70 € par mois"), 'price': '1670'},

                    {'option': gettext("Non - 50 €"), 'price': '5000'} 
                ]}
            ];
        };
    };

    show(tree[0]);
}

function show(tree) {
    $('.choices').html(
            '<h3>' + tree['question'] + '</h3>'
    );

    $.each(tree['children'], function(index, child) {
        $('.choices').append(
            '<label class="radio-inline">' + 
                '<input class="selector" type="radio" name=' + tree['name'] + ' index=' + index + '>' + child['option'] + 
            '</label>'
        );
        trees.push(child);
        $('input[name=' + tree['name'] + '][index=' + index + ']').attr('tree', Object.keys(trees).length - 1);
    });
};