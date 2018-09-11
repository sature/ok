/**
 * 
 */
var upColor = '#00da3c';
var downColor = '#ec0000';

function FormatDateTime(time) {
    var date = new Date(parseInt(time));
    var y = date.getFullYear();
    var m = date.getMonth() + 1;
    m = m < 10 ? ('0' + m) : m;
    var d = date.getDate();
    d = d < 10 ? ('0' + d) : d;
    var h = date.getHours();
    h = h < 10 ? ('0' + h) : h;
    var minute = date.getMinutes();
    var second = date.getSeconds();
    minute = minute < 10 ? ('0' + minute) : minute;
    second = second < 10 ? ('0' + second) : second;
    return y + '-' + m + '-' + d + ' ' + h + ':' + minute + ':' + second;
}

function splitData(rawData) {
	var categoryData = []
	var values = []
	var volumes = []
	for (var i = 0; i < rawData.data.length; i++) {
		categoryData.push(FormatDateTime(rawData.index[i]))
		volumes.push([i, rawData.data[i].splice(4, 1)[0], rawData.data[i][0] > rawData.data[i][3] ? 1 : -1])
					//            open                close               low                high
		values.push([rawData.data[i][0], rawData.data[i][3], rawData.data[i][2], rawData.data[i][1]])
	}
	
    return {
        categoryData: categoryData,
        values: values,
        volumes: volumes
    };
}

function calculateMA(dayCount, data) {
    var result = [];
    for (var i = 0, len = data.values.length; i < len; i++) {
        if (i < dayCount) {
            result.push('-');
            continue;
        }
        var sum = 0;
        for (var j = 0; j < dayCount; j++) {
            sum += data.values[i - j][1];
        }
        result.push(+(sum / dayCount).toFixed(3));
    }
    return result;
}

function addK(chart, name, categoryData, data, volume) {

    o = chart.getOption()

    o.legend[0].data.push(name)

    o.xAxis.push({
        type: 'category',
        data: categoryData,
        scale: true,
        boundaryGap : false,
        axisLine: {onZero: false},
        splitLine: {show: false},
        splitNumber: 20,
        min: 'dataMin',
        max: 'dataMax',
        axisPointer: {
            z: 100
        }
    })
    o.xAxis.push({
        type: 'category',
        gridIndex: 1,
        data: categoryData,
        scale: true,
        boundaryGap : false,
        axisLine: {onZero: false},
        axisTick: {show: false},
        splitLine: {show: false},
        axisLabel: {show: false},
        splitNumber: 20,
        min: 'dataMin',
        max: 'dataMax'
    })

    o.yAxis.push({
        scale: true,
        splitArea: {
            show: true
        }
    })
    o.yAxis.push({
        scale: true,
        gridIndex: 1,
        splitNumber: 2,
        axisLabel: {show: false},
        axisLine: {show: false},
        axisTick: {show: false},
        splitLine: {show: false}
    })

    o.dataZoom.push({
        type: 'inside',
        xAxisIndex: [0, 1],
        start: 90,
        end: 100
    })
    o.dataZoom.push({
        show: true,
        xAxisIndex: [0, 1],
        type: 'slider',
        top: '85%',
        start: 90,
        end: 100
    })

    o.series.push({
        name: name,
        type: 'candlestick',
        data: data,
        itemStyle: {
            normal: {
                color: upColor,
                color0: downColor,
                borderColor: null,
                borderColor0: null
            }
        },
        tooltip: {
            formatter: function (param) {
                param = param[0];
                return [
                    'Date: ' + param.name + '<hr size=1 style="margin: 3px 0">',
                    'Open: ' + param.data[0] + '<br/>',
                    'Close: ' + param.data[1] + '<br/>',
                    'Lowest: ' + param.data[2] + '<br/>',
                    'Highest: ' + param.data[3] + '<br/>'
                ].join('');
            }
        }
    })
    o.series.push({
        name: 'Volume',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volume
    })

    chart.setOption(option = o, true)
}

function addSeries(chart, name, data) {
    o = chart.getOption()
    o.legend[0].data.push(name)
    o.series.push({
        name: name,
        type: 'line',
        data: data,
        smooth: true,
        showSymbol: false,
        lineStyle: {
            normal: {opacity: 0.5}
        }
    })
    chart.setOption(option = o, true);
}

myChart = echarts.init(document.getElementById('echarts_main'));
myChart.setOption(option = {
    backgroundColor: '#fff',
    animation: false,
    legend: {
        bottom: 5,
        left: 'center',
        data: []
    },
    tooltip: {
        trigger: 'axis',
        axisPointer: {
            type: 'cross'
        },
        backgroundColor: 'rgba(245, 245, 245, 0.8)',
        borderWidth: 1,
        borderColor: '#ccc',
        padding: 10,
        textStyle: {
            color: '#000'
        },
        position: function (pos, params, el, elRect, size) {
            var obj = {top: 10};
            obj[['left', 'right'][+(pos[0] < size.viewSize[0] / 2)]] = 30;
            return obj;
        }
        // extraCssText: 'width: 170px'
    },
    axisPointer: {
        link: {xAxisIndex: 'all'},
        label: {
            backgroundColor: '#777'
        }
    },
    toolbox: {
        feature: {
            dataZoom: {
                yAxisIndex: false
            },
            brush: {
                type: ['lineX', 'clear']
            }
        }
    },
    visualMap: {
        show: false,
        seriesIndex: 5,
        dimension: 2,
        pieces: [{
            value: 1,
            color: downColor
        }, {
            value: -1,
            color: upColor
        }]
    },
    grid: [
        {
            left: '10%',
            right: '8%',
            height: '50%'
        },
        {
            left: '10%',
            right: '8%',
            top: '63%',
            height: '16%'
        }
    ],
    xAxis: [],
    yAxis: [],
    dataZoom: [],
    series: []
}, true);

$.get('/strategy/0', function(strategy) {

    k = strategy.k
    params = [
        'exchange=' + k['exchange'],
        'symbol='   + k['symbol'].replace('/','_').toLowerCase(),
        'type='     + k['type'],
        'period='   + k['period']
    ].join('&')

    $.get('/k?' + params, function (rawData) {
        var data = splitData(rawData.k);
        name = [
            k['exchange'],
            k['symbol'].replace('/','_').toLowerCase(),
            k['type'],
            k['period'],
            'K'
        ].join(' ')

        addK(myChart, name, data.categoryData, data.values, data.volumes)
//        addSeries(myChart, 'MA7', calculateMA(7, data))
//        addSeries(myChart, 'MA30', calculateMA(30, data))
    });
})
