; benchmark generated from python API
(set-info :status unknown)
(declare-fun c () (_ BitVec 8))
(declare-fun a () (_ BitVec 8))
(declare-fun b () (_ BitVec 8))
(assert
 (let ((?x50 ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) c)))))))))
(let ((?x12 (bvadd ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) b))) ((_ zero_extend 1) ((_ extract 6 0) ((_ extract 7 0) a))))))
(let ((?x37 ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ((_ extract 7 0) ?x12)))))))))
(let (($x159 (and (distinct (ite (bvsge a (_ bv0 8)) (_ bv1 1) (_ bv0 1)) (_ bv0 1)) true)))
(let ((?x156 (ite $x159 (bvadd ((_ extract 7 0) (ite (bvslt a (_ bv0 8)) (bvneg a) a)) ((_ extract 7 0) b)) c)))
(and (distinct ?x156 (ite $x159 ?x37 ?x50)) true)))))))
(check-sat)
