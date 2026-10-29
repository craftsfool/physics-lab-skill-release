function lab_origin_style(fig, outputBase)
% Apply lab-report style and export an existing figure without changing data.
% Usage: lab_origin_style(gcf, fullfile(outputFolder, '01_result'))
% The caller supplies measurement, model, theory, labels, and legends.
arguments
    fig (1,1) matlab.ui.Figure
    outputBase (1,:) char
end
set(fig,'Color','w');
cart=findall(fig,'Type','axes');
for ax=cart'
    set(ax,'FontName','Times New Roman','FontSize',12,'LineWidth',1.0,...
        'Box','on','TickDir','in','XMinorTick','on','YMinorTick','on');
    ax.Toolbar.Visible='off';
end
polar=findall(fig,'Type','polaraxes');
for ax=polar'
    ax.FontName='Times New Roman'; ax.FontSize=12; ax.LineWidth=1;
    ax.GridColor=[.65 .65 .65]; ax.GridAlpha=.45;
    ax.Toolbar.Visible='off';
end
folder=fileparts(outputBase);
if ~isempty(folder) && ~exist(folder,'dir'), mkdir(folder); end
% Do not overwrite previous outputs without an explicit caller decision.
for ext={'.png','.pdf','.fig'}
    if isfile([outputBase ext{1}])
        error('lab:OutputExists','Output already exists: %s',[outputBase ext{1}]);
    end
end
drawnow;
exportgraphics(fig,[outputBase '.png'],'Resolution',300,'BackgroundColor','white');
exportgraphics(fig,[outputBase '.pdf'],'ContentType','vector','BackgroundColor','white');
savefig(fig,[outputBase '.fig']);
end
